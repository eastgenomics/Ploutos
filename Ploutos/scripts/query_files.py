"""This script is testing queries for file searching in DNAnexus
It currently gets all files in DNAnexus, puts info into a dict grouped by project, then puts files into a df then calculates total size and cost for unique projects and total projects (with dups) per file state (live or archived)
Finally saves to a json"""
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

today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/", "-")
year, month = int(today_date.split("-")[0]), int(today_date.split("-")[1])

def run():
    """Main function"""

    start = time()

    # Log into DNAnexus
    login(settings.DX_TOKEN)

    # Get projects from DNAnexus and put into dict and list
    all_projects, proj_list = get_projects()

    # Get all the files per proj and put into list of dicts
    project_file_dicts_list = threadify(proj_list, get_files)

    # Make a dataframe from all those files
    file_df = make_file_df(project_file_dicts_list)

    # Counting how many projs are lost due to empty making the df for info
    unique_without_empty_projs, empty_projs = count_how_many_lost(file_df, proj_list)

    # Make a project df
    proj_df = make_proj_df(all_projects)

    # Merge the files and proj dfs
    merged_df = merge_files_and_proj_dfs(file_df, proj_df)

    # Remove duplicates to create a unique df
    unique_df = remove_duplicates(merged_df, unique_without_empty_projs)

    # Group by project for total size in the unique df and rename file states
    unique_grouped_df = group_by_project_and_rename(unique_df, 'unique')

    # Group by project for total size in the df which contains dups and rename file states
    total_grouped_df = group_by_project_and_rename(merged_df, 'total')

    # Calculate total cost for unique files per proj
    unique_sum_df = calculate_totals(unique_grouped_df, "unique")

    # Calculate total cost for all files per proj (with dups)
    total_sum_df = calculate_totals(total_grouped_df, "total")

    # Merge unique and total (with dups) together, adding missing rows
    merged_total_df = merge_together_add_empty_rows(unique_sum_df, total_sum_df)

    # Add back in projects with no files as zeros
    final_all_projs_df = add_empty_projs_back_in(empty_projs, merged_total_df)

    # Write final storage file to json
    final_dict = put_into_dict_write_to_file(final_all_projs_df)

    end = time()
    total = end - start
    print(f"Total time was {total}")
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))

def login(token):
    """Log into DNAnexus using token defined in Django settings"""
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

def no_of_days_in_month(year, month):
    """Get the number of days in a month by the year and month"""
    return monthrange(year, month)[1]

def get_projects():
    """Get all projects in DNAnexus"""
    project_response = list(dx.find_projects(
        billed_to= settings.ORG, level='VIEW', describe=True))

    project_ids_list = []

    all_projects = defaultdict(dict)
    for project in project_response:
        project_id = project['id']
        project_ids_list.append(project_id)
        all_projects[project_id]['dx_id'] = project['describe']['id']
        all_projects[project_id]['name'] = project['describe']['name']
        all_projects[project_id]['created_by'] = project['describe']['createdBy']['user']
        all_projects[project_id]['created_epoch'] = project['describe']['created']
        all_projects[project_id]['created'] = dt.datetime.fromtimestamp(
            (project['describe']['created']) / 1000).strftime('%Y-%m-%d')

    return all_projects, project_ids_list

def get_files(proj):
    """Gets files per proj and their info and puts into a nested dict"""

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
    list_of_project_file_dicts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for project in project_list:
            futures.append(executor.submit(get_files_function, proj=project))
        for future in concurrent.futures.as_completed(futures):
            list_of_project_file_dicts.append(future.result())

    return list_of_project_file_dicts

def make_file_df(list_project_files_dictionary):
    """Get all the files from the list of files per proj dict and put into a df"""
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
    """Count how many projects had no files"""
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
    """Make a df of projects with the proj ID and epoch created"""

    # Create a df with a row for each project from the dict 
    projects_df = pd.DataFrame.from_dict(proj_dict.values())

    # Drop other columns as not needed
    projects_df = projects_df.drop(columns=['name', 'created_by', 'created'])
    # Rename dx_id for easy merging
    projects_df = projects_df.rename({'dx_id': 'project'}, axis='columns')

    return projects_df

def merge_files_and_proj_dfs(file_df, proj_df):
    """Merge the two dataframes together so that the oldest project can be found"""

    files_with_proj_created = pd.merge(file_df, proj_df, on=["project"])

    # Replace the state 'archival' to live for easy grouping later as they're technically charged as live
    files_with_proj_created['state'] = files_with_proj_created['state'].str.replace('archival', 'live')

    return files_with_proj_created

def remove_duplicates(merged_df, unique_without_empty_projs):
    # Sort rows by lowest epoch created time (oldest), drop those with duplicate file IDs 
    # Keeping only the file in the oldest project
    unique_df = merged_df.sort_values('created_epoch', ascending=True).drop_duplicates('id').sort_index()

    unique_projects_after_dups_removed = len(unique_df.project.unique())

    total_removed = unique_without_empty_projs - unique_projects_after_dups_removed
    print(f"{total_removed} projects are no longer in the table as they only contained duplicate files")
    return unique_df

def group_by_project_and_rename(df_name, string_to_replace):
    # Group by project and file state and sum the size column to get total size (with duplicates)
    grouped_df = df_name.groupby(['project','state']).agg(size=('size', 'sum')).reset_index()

    # Replace the values with unique_ as it makes it easier to merge later
    grouped_df['state'] = grouped_df['state'].str.replace('live', string_to_replace+"_live")
    grouped_df['state'] = grouped_df['state'].str.replace('archived', string_to_replace+"_archived")

    return grouped_df

def calculate_totals(my_grouped_df, type):
    days_in_month = no_of_days_in_month(year, month)
    # If the state of the file is live, convert total size to GB and times by storage cost per month
    # Then divide by the number of days in current month
    # Else if state not live (archived) then times by archived storage cost price

    my_grouped_df['cost'] = np.where(my_grouped_df['state'] == type+"_live",
                                            my_grouped_df['size'] / (2**30) * settings.LIVE_STORAGE_COST_MONTH / days_in_month,
                                            my_grouped_df['size'] / (2**30) * settings.ARCHIVED_STORAGE_COST_MONTH / days_in_month)

    return my_grouped_df

def merge_together_add_empty_rows(df1, df2):
    # Merge the two together to have unique and total costs in one df
    total_merged_df = pd.concat([df1, df2], ignore_index=True, sort=True)

    iterables = [total_merged_df['project'].unique(),total_merged_df['state'].unique()]
    total_merged_df = total_merged_df.set_index(['project','state'])
    total_merged_df = total_merged_df.reindex(index=pd.MultiIndex.from_product(iterables, names=['project', 'state']), fill_value=0).reset_index()

    return total_merged_df

def add_empty_projs_back_in(empty_projs, total_merged_df):
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
    all_proj_dict = {n: grp.loc[n].to_dict('index') for n, grp in final_all_projs_df.set_index(['project', 'state']).groupby(level='project')}

    final_project_storage_totals = json.dumps(all_proj_dict, indent=4)

    with open("project_storage_totals.json", "w") as outfile:
        outfile.write(final_project_storage_totals)

    return all_proj_dict
