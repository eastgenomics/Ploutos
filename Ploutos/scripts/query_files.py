"""
This script gets all files from DNAnexus into a dict grouped by project, then inserts all files into a df to calculates total size and cost for unique projects and total projects (with dups) per file state (live or archived)
Finally saves to a json
"""

import concurrent.futures
import datetime as dt
import json
import numpy as np
import pandas as pd
import sys
import dxpy as dx

from calendar import monthrange
from collections import defaultdict
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
from django.apps import apps
from django.conf import settings
from time import time, localtime, strftime


def run():
    """Essentially a main function"""

    start = time()

    login(settings.DX_TOKEN)
    all_projects, proj_list = get_projects()
    project_file_dicts_list = threadify(proj_list, get_files)
    file_df = make_file_df(project_file_dicts_list)
    unique_without_empty_projs, empty_projs = count_how_many_lost(file_df, proj_list)
    proj_df = make_proj_df(all_projects)
    merged_df = merge_files_and_proj_dfs(file_df, proj_df)
    unique_df = remove_duplicates(merged_df, unique_without_empty_projs)
    unique_grouped_df = group_by_project_and_rename(unique_df, 'unique')
    total_grouped_df = group_by_project_and_rename(merged_df, 'total')
    unique_sum_df = calculate_totals(unique_grouped_df, 'unique')
    total_sum_df = calculate_totals(total_grouped_df, 'total')
    merged_total_df = merge_together_add_empty_rows(unique_sum_df, total_sum_df)
    final_all_projs_df = add_empty_projs_back_in(empty_projs, merged_total_df)
    final_dict = put_into_dict_write_to_file(final_all_projs_df)

    end = time()
    total = end - start
    print(f"Total time was {total}")
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))

def login(token):
    """
        Logs into DNAnexus
        Parameters
        ----------
        token : str
            authorisation token for DNAnexus, from settings.py

        Returns
        -------
        None
    """

    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": token
    }

    dx.set_security_context(DX_SECURITY_CONTEXT)

    try:
        dx.api.system_whoami()
        print("DNAnexus login successful")
    except:
        print("Error with DNAnexus login")
        sys.exit(1)

def no_of_days_in_month():
    """
    Get days in the month for calculations later
    Parameters
    ----------
    none

    Returns
    -------
     day_count : int
        number of days in current month
    """
    today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/", "-")
    year, month = int(today_date.split("-")[0]), int(today_date.split("-")[1])
    day_count = monthrange(year, month)[1]

    return day_count

def get_projects():
    """
    Get all projects in DNAnexus, stores their id and time they were created (epoch - int)

    Parameters
    ----------
    none

    Returns
    -------
     all_projects : collections.defaultdict
        dictionary with project as key and relevant info
    """
    project_response = list(dx.find_projects(
        billed_to= settings.ORG, level='VIEW', describe=True))

    project_ids_list = []

    all_projects = defaultdict(dict)
    for project in project_response:
        project_id = project['id']
        project_ids_list.append(project_id)
        all_projects[project_id]['project'] = project['describe']['id']
        all_projects[project_id]['created_epoch'] = project['describe']['created']

    return all_projects, project_ids_list

def get_files(proj):
    """
    Get all files for the project in DNAnexus, storing each file and its size, name and archival state. Is used with ThreadExecutorPool

    Parameters
    ----------
    proj : entry in list

    Returns
    -------
     project_files_dict : collections.defaultdict
        dictionary with all the files per project
    e.g. 
    [ {"project-X": 
     {"files": 
      [
          {
        'file_id': 'file-1', 'name': "IamFile1.json", 'size': 4803, 
      'archivalState': 'live'
    }, 
    {
        'file_id': 'file-2', 'name': "IamFile2.json", 'size': 702, 
      'archivalState': 'archived'
    }
      ]
     }},
    {'project-Y': 
     {"files": 
      [{
        'file_id': 'file-4', 'name': "IamFile4.json", 'size': 3281, 
      'archivalState': 'live'
      },
        {
            'file_id': 'file-1', 'name': "IamFile1.json", 'size': 4803, 
      'archivalState': 'live'
        }
      ]
    }}
      ]
    """

    # Find files in each project, only returning specified fields
    # Per project, create dict with info per file and add this to 'file' list
    # .get handles files with no size (e.g. .snapshot files) and sets this to zero
    project_files_dict = defaultdict(lambda: {"files": []})
    files = list(dx.search.find_data_objects(classname='file', project=proj, describe={
                    'fields': {'archivalState': True, 'size': True, 'name': True}}))
    for file in files:
        proj = file['project']
        project_files_dict[proj]["files"].append({"id": file["id"], "name": file["describe"]['name'], "size": file.get(
            'describe', {}).get('size', 0), "state": file['describe']['archivalState']})

    return project_files_dict

def threadify(project_list, get_files_function):
    """
    Use ThreadPoolExecutor on get_files() function

    Parameters
    ----------
    project_list : list
        list of all the projects in DNAnexus
    get_files_function: function
        the function which gets files per project

    Returns
    -------
     list_of_project_file_dicts : list
        list of dictionaries with all the files per project in each dict
    """
    list_of_project_file_dicts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for project in project_list:
            futures.append(executor.submit(get_files_function, proj=project))
        for future in concurrent.futures.as_completed(futures):
            list_of_project_file_dicts.append(future.result())

    return list_of_project_file_dicts

def make_file_df(list_project_files_dictionary):
    """
    Get all files from the list of files per proj dict and put into a df

    Parameters
    ----------
    list_project_files_dictionary : list
        list of dictionaries with all the files per project in each dict

    Returns
    -------
     file_df : pd.DataFrame
        dataframe with row for each file including project, file ID, size and state
    """

    rows = []
    # For each project dictionary with its associated files
    for project_dict in list_project_files_dictionary:
        # For the project and its associated files
        for k, v  in project_dict.items():
            # Get the file info
            data_row = v['files']
            # Assign the project as the parent key
            project = k
            
            # Add the project name to the row 'project'
            for row in data_row:
                row['project'] = project
                # Append each file's info as info to the other columns
                rows.append(row)

    # Convert to data frame
    # Drop the name column as it's not used later
    file_df = pd.DataFrame(rows)
    file_df = file_df.drop(columns=['name'])
    
    return file_df

def count_how_many_lost(df_of_files, projs_list):
    """
    Count how many projects are lost when making the file df because they have no files

    Parameters
    ----------
    df_of_files : pd.DataFrame
        dataframe with row for each file including project, file ID, size and state
    projs_list : list
        list of all projects in DNAnexus

    Returns
    -------
    unique_after_empty_projs_removed : int
        how many unique projects there are currently in the files df
    empty_projs : list
        a list of the projects which do not have any files
    """
    how_many_unique  = list(df_of_files.project.unique())
    unique_after_empty_projs_removed = len(how_many_unique)
    #print(f"There are {unique_after_empty_projs_removed} unique projects in the df")

    total_projs = len(projs_list)
    #print(f"There are {total_projs} total projects")

    empty_projs = [i for i in projs_list if i not in how_many_unique]
    how_many_empty = len(empty_projs)
    print(f"There are {how_many_empty} projects where no files were found and so they have not been added to the df")
    return unique_after_empty_projs_removed, empty_projs

def make_proj_df(proj_dict):
    """
    Make a project dataframe with project and its created for merging

    Parameters
    ----------
    proj_dict : collections.defaultdict
        project dictionary from earlier

    Returns
    -------
    projects_df : pd.DataFrame
        a dataframe with project ID and its epoch created time
    """

    # Create a df with a row for each project from the dict 
    projects_df = pd.DataFrame.from_dict(proj_dict.values())

    return projects_df

def merge_files_and_proj_dfs(file_df, proj_df):
    """
    Merge the files and projects dfs together so oldest project can be found
    Parameters
    ----------
    file_df : pd.DataFrame
        dataframe of the files
    proj_df : pd.DataFrame
        dataframe of the projects and their created
    Returns
    -------
    files_with_proj_created : pd.DataFrame
        merged dataframe with each file including the associated project's created
    """

    files_with_proj_created = pd.merge(file_df, proj_df, on=["project"])

    # Replace the state 'archival' to live for easy grouping later as they're technically charged as live
    files_with_proj_created['state'] = files_with_proj_created['state'].str.replace('archival', 'live')

    return files_with_proj_created

def remove_duplicates(merged_df, unique_without_empty_projs):
    """
    Remove the duplicate files which are found in >1 project by oldest project
    Parameters
    ----------
    merged_df : pd.DataFrame
        merged dataframe for files with projects created
    unique_without_empty_projs : int
        the number of projects that were in the files df when first created
        
    Returns
    -------
    unique_df : pd.DataFrame
        dataframe with duplicate files removed
    """
    # Sort rows by lowest epoch created time (oldest), drop those with duplicate file IDs 
    # Keeping only the file in the oldest project
    unique_df = merged_df.sort_values('created_epoch', ascending=True).drop_duplicates('id').sort_index()

    unique_projects_after_dups_removed = len(unique_df.project.unique())

    total_removed = unique_without_empty_projs - unique_projects_after_dups_removed
    print(f"{total_removed} projects are no longer in the table as they only contained duplicate files")
    return unique_df

def group_by_project_and_rename(df_name, string_to_replace):
    """
    Group the dataframe by project to get total size per file state
    ----------
    df_name : pd.DataFrame
        the dataframe you want to group (unique or total)
    string_to_replace : str
        'unique' or 'total'
        
    Returns
    -------
    grouped_df : pd.DataFrame
        dataframe grouped by project, state (e.g. total_live) which gives the aggregated size
    """
    # Group by project and file state and sum the size column to get total size (with duplicates)
    grouped_df = df_name.groupby(['project','state']).agg(size=('size', 'sum')).reset_index()

    # Replace the values with unique_ as it makes it easier to merge later
    grouped_df['state'] = grouped_df['state'].str.replace('live', string_to_replace+"_live")
    grouped_df['state'] = grouped_df['state'].str.replace('archived', string_to_replace+"_archived")

    return grouped_df

def calculate_totals(my_grouped_df, type):
    """
    Calculate the total cost of storing per project by file state through rates defined in CREDENTIALS.json
    ----------
    my_grouped_df : pd.DataFrame
        the dataframe which is grouped by project and state with aggregated total size
    type : str
        'unique' or 'total'
        
    Returns
    -------
    grouped_df : pd.DataFrame
        dataframe with calculated daily storage cost grouped by project and state with columns project, state, size, cost
    """
    days_in_month = no_of_days_in_month()
    # If the state of the file is live, convert total size to GB and times by storage cost per month
    # Then divide by the number of days in current month
    # Else if state not live (archived) then times by archived storage cost price

    my_grouped_df['cost'] = np.where(my_grouped_df['state'] == type+"_live",
                                            my_grouped_df['size'] / (2**30) * settings.LIVE_STORAGE_COST_MONTH / days_in_month,
                                            my_grouped_df['size'] / (2**30) * settings.ARCHIVED_STORAGE_COST_MONTH / days_in_month)

    return my_grouped_df

def merge_together_add_empty_rows(df1, df2):
    """
    Merge together the two dataframes to easily make dict at end and add zeros for any file state categories which don't exist
    ----------
    df1 : pd.DataFrame
        the dataframe with costs for unique files per project
    type : str
        the dataframe with costs for all files per project
        
    Returns
    -------
    total_merged_df : pd.DataFrame
        merged dataframe with project, all file states (total_live, total_archived, unique_live, unique_archived), cost and size with zeros if did not exist
    """
    # Merge the two together to have unique and total costs in one df
    total_merged_df = pd.concat([df1, df2], ignore_index=True, sort=True)

    # If there isn't a particular file state for a project
    # Add missing rows for each file state and set the size and cost to zero
    iterables = [total_merged_df['project'].unique(),total_merged_df['state'].unique()]
    total_merged_df = total_merged_df.set_index(['project','state'])
    total_merged_df = total_merged_df.reindex(index=pd.MultiIndex.from_product(iterables, names=['project', 'state']), fill_value=0).reset_index()

    return total_merged_df

def add_empty_projs_back_in(empty_projs, total_merged_df):
    """
    Add entries for projects which do not contain any files so all projects are represented
    ----------
    empty_projs : list
        list of projects which do not have any files
    total_merged_df : pd.DataFrame
        most complete df with projects, all file states per proj and total cost and size
        
    Returns
    -------
    final_all_projs_df : pd.DataFrame
        final dataframe with project, file state, total size and cost for all projects 
    """
    # For the projects that were removed at the beginning because they are empty
    # Create a list of dictionaries with all the fields as zero
    empty_project_rows = []

    for proj in empty_projs:
        empty_project_rows.append({'project': proj, 'state': 'total_live', 'cost':0, 'size': 0})
        empty_project_rows.append({'project': proj, 'state': 'total_archived', 'cost':0, 'size': 0})
        empty_project_rows.append({'project': proj, 'state': 'unique_live', 'cost':0, 'size': 0})
        empty_project_rows.append({'project': proj, 'state': 'unique_archived', 'cost':0, 'size': 0})

    # Append the projects with no files to the final merged dataframe
    final_all_projs_df = total_merged_df.append(empty_project_rows, ignore_index=True, sort=False)

    return final_all_projs_df

def put_into_dict_write_to_file(final_all_projs_df):
    """
    Put back into a dict for easy adding to the db
    ----------
    final_all_projs_df : pd.DataFrame
        final dataframe with project, file state, total size and cost for all projects
        
    Returns
    -------
    all_proj_dict : dict
        final dictionary with key project and nested keys total_live, total_archived, unique_live, unique_archived (and nested size and cost within) for all projects
    e.g. "project-XYZ": {
        "total_live": {
            "cost": 0.875400299678058,
            "size": 1133796550572
        },
        "total_archived": {
            "cost": 0.0,
            "size": 0
        },
        "unique_live": {
            "cost": 0.875400299678058,
            "size": 1133796550572
        },
        "unique_archived": {
            "cost": 0.0,
            "size": 0
        }
    }, "project-ABC": {
    ...
    }

    """
    all_proj_dict = {n: grp.loc[n].to_dict('index') for n, grp in final_all_projs_df.set_index(['project', 'state']).groupby(level='project')}

    final_project_storage_totals = json.dumps(all_proj_dict, indent=4)

    with open("project_storage_totals.json", "w") as outfile:
        outfile.write(final_project_storage_totals)

    return all_proj_dict
