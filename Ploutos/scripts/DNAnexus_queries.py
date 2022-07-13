"""
DNAnexus queries script
"""

import concurrent.futures
import datetime as dt
import numpy as np
import pandas as pd
import sys
import dxpy as dx

from calendar import monthrange
from collections import defaultdict
from functools import reduce

from django.conf import settings


def login() -> None:
    """
        Logs into DNAnexus
        Parameters
        ----------
        token : str
            authorisation token for DNAnexus, from settings.py
        Raises
        ------
        Error
            Raised when DNAnexus user authentification check fails
        Returns
        -------
        None
    """

    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": settings.DX_TOKEN
    }

    dx.set_security_context(DX_SECURITY_CONTEXT)

    try:
        dx.api.system_whoami()
        print("DNAnexus login successful")
    except Exception as e:
        print(f'Error logging into DNAnexus: {e}')
        sys.exit(1)

def no_of_days_in_month():
    """
    Get days in the month for calculations later
    Parameters
    ----------
    none
    Returns
    -------
     today_date : str
        today's date e.g. "06-06-2022"
     day_count : int
        number of days in current month
    """
    today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/", "-")
    year, month = int(today_date.split("-")[0]), int(today_date.split("-")[1])
    day_count = monthrange(year, month)[1]

    return today_date, day_count


def get_projects():
    """
    Get all projects in DNAnexus,
    stores their id and time they were created (epoch - int)

    Parameters
    ----------
    none

    Returns
    -------
     all_projects : collections.defaultdict
        dictionary with project as key and relevant info
    projects_ids_list : list
        all the project IDs in a list
    projects_df : pd.DataFrame
        dataframe with a row for each project
    """
    project_response = list(dx.find_projects(
        billed_to=settings.ORG,
        level='VIEW',
        describe={'fields': {
            'id': True, 'name': True, 'createdBy': True, 'created': True
            }
        }))

    # Put each into dict, turn epoch time into datetime YYYY-MM-DD
    project_ids_list = []
    list_projects_dicts = []
    for project in project_response:
        project_ids_list.append(project['id'])
        item = {
            'dx_id': project['describe']['id'],
            'name': project['describe']['name'],
            'created_by': project['describe']['createdBy']['user'],
            'created_epoch': project['describe']['created'],
            'created': dt.datetime.fromtimestamp(
                (project['describe']['created']) / 1000).strftime('%Y-%m-%d')}
        list_projects_dicts.append(item)

    # Create project data df, one project per row, keep only required columns
    projects_df = pd.DataFrame(list_projects_dicts)
    projects_df = projects_df.drop(columns=['name', 'created_by', 'created'])
    projects_df.rename(columns = {'dx_id':'project'}, inplace = True)

    return list_projects_dicts, project_ids_list, projects_df


def get_files(proj):
    """
    Get all files for the project in DNAnexus
    Storing each file and its size, name and archival state.
    Used with ThreadExecutorPool

    Parameters
    ----------
    proj : str
        given project to retrieve all files for

    Returns
    -------
     project_files_dict : collections.defaultdict
        dictionary with all the files and metadata per project

    """

    # Find files in each project, only returning specified fields
    # Per project, create dict with info per file and add this to 'file' list
    # .get handles files with no size (e.g. .snapshot files) and sets this to zero
    project_files_dict = defaultdict(lambda: {"files": []})
    files = list(dx.search.find_data_objects(
        classname='file', project=proj,
        describe={'fields': {
            'archivalState': True,
            'size': True,
            'name': True
        }}
    ))
    for file in files:
        proj = file['project']
        project_files_dict[proj]["files"].append({
            "id": file["id"],
            "name": file["describe"]['name'],
            "size": file.get('describe', {}).get('size', 0),
            "state": file['describe']['archivalState']
        })

    return project_files_dict


def threadify(project_list):
    """
    Use pool of threads to asynchronously get_files() on multiple projects

    Parameters
    ----------
    project_list : list
        list of all the projects in DNAnexus
    Returns
    -------
     list_of_project_file_dicts : list
        list of dictionaries with all the files per project in each dict
     e.g.
    [{
        'project-X': {'files': [
            {
                'file_id': 'file-1',
                'name': "IamFile1.json",
                'size': 4803,
                'archivalState': 'live'
            }, {
                'file_id': 'file-2',
                'name': "IamFile2.json",
                'size': 702,
                'archivalState': 'archived'
            }
        ]}
    },
    {
        'project-Y': {'files': [
            {
                'file_id': 'file-4',
                'name': "IamFile4.json",
                'size': 3281,
                'archivalState': 'live'
            }
        ]}
    }]
    """
    list_of_project_file_dicts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        # Submit the get_files function for a project
        for project in project_list:
            futures.append(executor.submit(get_files, proj=project))
        # Once all project files are retrieved, append the final dict  
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

    >>> make_file_df(all_files, all_projects)
    -------------------------------------------------------------------
    List of files with describe data
    -------------------------------------------------------------------
     e.g.
    [{
        'project-X': {'files': [
            {
                'file_id': 'file-1',
                'name': "IamFile1.json",
                'size': 4803,
                'archivalState': 'live'
            }, {
                'file_id': 'file-2',
                'name': "IamFile2.json",
                'size': 702,
                'archivalState': 'archived'
            }
        ]}
    },
    {
        'project-Y': {'files': [
            {
                'file_id': 'file-4',
                'name': "IamFile4.json",
                'size': 3281,
                'archivalState': 'live'
            }
        ]}
    }]
    --------------------------------------------------------------------
                                      |
                                      |
                                      ▼
                                  DataFrame
    +-----------+--------+---------------+---------------+------+
    |  project  |   id   |     name      | archivalState | size |
    +-----------+--------+---------------+---------------+------+
    | project-X | file-1 | IamFile1.json | live          | 4803 |
    | project-X | file-2 | IamFile2.json | archived      |  702 |
    | project-Y | file-4 | IamFile4.json | live          | 3281 |
    +-----------+--------+---------------+---------------+------+
    """

    rows = []
    # For each project dictionary with its associated files
    for project_dict in list_project_files_dictionary:
        # For the project and its associated files
        for project, data in project_dict.items():
            # Get the file info
            data_row = data['files']

            # Add the project name to the row 'project'
            for row in data_row:
                row['project'] = project
                # Append each file's info as info to the other columns
                rows.append(row)

    # Convert to data frame
    # Drop the name column as it's not used later
    file_df = pd.DataFrame(rows)
    #file_df.drop(columns=['name'], inplace=True)

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
    how_many_unique = list(df_of_files.project.unique())
    unique_after_empty_projs_removed = len(how_many_unique)
    #print(f"There are {unique_after_empty_projs_removed} unique projects in the df")

    total_projs = len(projs_list)
    #print(f"There are {total_projs} total projects")

    empty_projs = [i for i in projs_list if i not in how_many_unique]
    how_many_empty = len(empty_projs)
    print(f"There are {how_many_empty} projects with no files so they weren't added to the df")
    return unique_after_empty_projs_removed, empty_projs

def merge_files_and_proj_dfs(file_df, proj_df):
    """
    Merge the files and projects dfs together so oldest project can be found

    Parameters
    ----------
    file_df : pd.DataFrame
        dataframe of the files
    proj_df : pd.DataFrame
        dataframe of the projects and their epoch time created

    Returns
    -------
    files_with_proj_created : pd.DataFrame
        merged dataframe with each file including
        its associated project's created time.

    -------------------------------------------------------------------
    Data frame with all files. + Data frame with all projects and created_epoch
    -------------------------------------------------------------------
     e.g.
    +-----------+--------+---------------+---------------+------+
    |  project  |   id   |     name      | archivalState | size |
    +-----------+--------+---------------+---------------+------+
    | project-X | file-1 | IamFile1.json | live          | 4803 |
    | project-X | file-2 | IamFile2.json | archived      |  702 |
    | project-Y | file-4 | IamFile4.json | live          | 3281 |
    +-----------+--------+---------------+---------------+------+

                                +

                            DataFrame
    +-----------+---------------+
    |  project  | created_epoch |
    +-----------+---------------+
    | project-X |    1649941566 |
    | project-Y |    1659899291 |
    +-----------+---------------+

    --------------------------------------------------------------------
                                      |
                                      |
                                      ▼

                                  DataFrame
    +-----------+--------+---------------+---------------+------+---------------+
    |  project  |   id   |     name      | archivalState | size | created_epoch |
    +-----------+--------+---------------+---------------+------+---------------+
    | project-X | file-1 | IamFile1.json | live          | 4803 |    1649941566 |
    | project-X | file-2 | IamFile2.json | archived      |  702 |    1649941566 |
    | project-Y | file-4 | IamFile4.json | live          | 3281 |    1659899291 |
    +-----------+--------+---------------+---------------+------+---------------+
    """

    files_with_proj_created = pd.merge(file_df, proj_df, on=["project"])

    # Replace the state 'archival' to live for easy grouping later
    # As they're technically charged as live
    files_with_proj_created['state'] = files_with_proj_created['state'].str.replace(
        'archival', 'live')
    # Replace unarchiving with archived so adding missing rows works
    # See - https://documentation.dnanexus.com/user/objects/archiving-files
    # This explains the archiving process - unarchiving files are still currently archived.
    files_with_proj_created['state'] = files_with_proj_created['state'].str.replace(
        'unarchiving', 'archived')

    return files_with_proj_created

def remove_duplicates(merged_df, unique_without_empty_projs):
    """
    Remove duplicate files, attributing a file only to the oldest project
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
    unique_df = merged_df.sort_values(
        'created_epoch', ascending=True).drop_duplicates('id').sort_index()

    unique_projects_after_dups_removed = len(unique_df.project.unique())

    total_removed = unique_without_empty_projs - unique_projects_after_dups_removed
    print(f"{total_removed} projects are no longer in the table as they only contained duplicate files")
    return unique_df

def make_file_type_aggregate_df(unique_df, file_type_str):
    """
    Make dataframes for each file type aggregating
    The size and count of that file type per project with one row per state
    ----------
    unique_df : pd.DataFrame
        dataframe with only unique files from remove_duplicates()
    file_type_str : str
        the file type to search for in projects, e.g. "fastq"

    Returns
    -------
    size_count_df_grouped : pd.DataFrame
        dataframe aggregating size and count for that file type
    e.g.
    +---------+--------------+---------+-----------+----------+---------------+
    |   id    |    name      |  size   |  state    | project  | created_epoch |
    +---------+--------------+---------+-----------+----------+---------------+
    | file-X  | file1.vcf    |  29387  | live      | proj-X   | 1653411917000 |
    | file-Y  | file2.bam    | 161304  | live      | proj-X   | 1653411917000 |
    | file-Z  | file3.fastq  | 310211  | archived  | proj-X   | 1653411917000 |
    +---------+--------------+---------+-----------+----------+---------------+
                                |
                                ▼
    +------------+-----------+-------------+-------------+
    |  project   |  state    | fastq_size  | fastq_count |
    +------------+-----------+-------------+-------------+
    | project-X  | live      | 9267688059  |          10 |
    | project-Y  | archived  |  481747221  |           2 |
    | project-Y  | live      | 1372413129  |          32 |
    +------------+-----------+-------------+-------------+
    """
    # If searching for fastqs or vcfs search for this in file name + .gz
    # Group by project + state, aggregate size and count of file type per proj
    if file_type_str == 'fastq' or file_type_str == 'vcf':
        file_types = [f'{file_type_str}', f'{file_type_str}.gz']
        size_count_df_grouped = unique_df.loc[
            np.logical_or(
                unique_df.name.str.endswith(f'.{file_types[0]}'),
                unique_df.name.str.endswith(f'.{file_types[1]}')
            )
        ].groupby(['project', 'state']).agg(
            {'size' : ['sum', 'count']}
        ).reset_index()

    # If searching for bams search for just that extension
    # Group by project + state, aggregate size and count of file type per proj
    elif file_type_str == 'bam':
        size_count_df_grouped = unique_df.loc[
            unique_df.name.str.endswith(f'.{file_type_str}')
        ].groupby(['project','state'], as_index=False).agg(
            {'size' : ['sum', 'count']}
        )

    # Rename columns as flat from multiIndex
    size_count_df_grouped.columns = size_count_df_grouped.columns.droplevel(0)
    size_count_df_grouped = size_count_df_grouped.rename_axis(None, axis=1)
    size_count_df_grouped.columns = [
        'project', 'state', f'{file_type_str}_size', f'{file_type_str}_count'
    ]

    return size_count_df_grouped

def add_missing_states_projects_file_types(
    file_df, file_type_agg_df, file_type
):
    """
    Add in states that are missing per project as zeros then
    Add projects which are missing entirely from the file specific df as zeros
    ----------
    file_df : pd.DataFrame
        dataframe with all the projects and their files from make_file_df()
    file_type_agg_df : pd.DataFrame
        file type specific df which has file type size and count per project
    file_type : str
        the file type from the df which is entered e.g. "fastq"

    Returns
    -------
    aggregated_file_type_all_projs : pd.DataFrame
        dataframe including two rows (live and archived) per project
        with aggregated size and count for the file type for all projects
    e.g.
    +------------+-----------+-------------+-------------+
    |  project   |  state    | fastq_size  | fastq_count |
    +------------+-----------+-------------+-------------+
    | project-X  | live      | 9267688059  |          10 |
    | project-Y  | archived  |  481747221  |           2 |
    | project-Y  | live      | 1372413129  |          32 |
    +------------+-----------+-------------+-------------+
                            |
                            ▼
    +------------+-----------+-------------+-------------+
    |  project   |  state    | fastq_size  | fastq_count |
    +------------+-----------+-------------+-------------+
    | project-X  | live      | 9267688059  |          10 |
    | project-X  | archived  |  481747221  |           2 |
    | project-Y  | live      | 1372413129  |          32 |
    | project-Y  | archived  |           0 |           0 |
    +------------+-----------+-------------+-------------+
    """
    # Get unique values of projects and states
    iterables = [
        file_type_agg_df['project'].unique(),
        file_type_agg_df['state'].unique()
    ]

    # Add in a row for a state for a project it doesn't exist
    # With size and count as zero
    states_filled_in = file_type_agg_df.set_index(['project','state'])
    states_filled_in = states_filled_in.reindex(
        index=pd.MultiIndex.from_product(
            iterables, names=['project', 'state']
        ), fill_value=0
    ).reset_index()

    # Find the projects that are in the original file df of all files
    # Which might only contain duplicates or not that file type
    how_many_unique_projects = list(file_df.project.unique())
    projects_left_in_this_df = list(states_filled_in.project.unique())
    empty_projs = [
        i for i in how_many_unique_projects
        if i not in projects_left_in_this_df
    ]

    # Append two dicts for live and archived rows
    # For the projects without that file type
    # (Or with only duplicates) to list, setting file size + count to zero
    empty_project_rows = []
    for proj in empty_projs:
        empty_project_rows.append(
            {
                'project': proj, 'state': 'live',
                f'{file_type}_size': 0, f'{file_type}_count': 0
            }
        )
        empty_project_rows.append(
            {
                'project': proj, 'state': 'archived',
                f'{file_type}_size': 0, f'{file_type}_count': 0
            }
        )

    # Add the rows to the df for those projects
    aggregated_file_type_all_projs = states_filled_in.append(
        empty_project_rows, ignore_index=True, sort=False
    )

    return aggregated_file_type_all_projs

def generate_merged_file_df(list_of_aggregated_dataframes):
    """
    Generate a df in wide format with 1 row / project and all file types+states
    With their sizes and counts
    ----------
    list_of_aggregated_dataframes : list
        list of dataframes having two rows per project + tot file size + count
        e.g. [vcf_final, bam_final, fastq_final]

    Returns
    -------
    aggregated_all_file_types_df : pd.DataFrame
        dataframe with one row per proj and 12 columns, 4 per file type
    +-----------+----------+------------+-------------+
    |  project  |  state   | fastq_size | fastq_count |
    +-----------+----------+------------+-------------+
    | project-X | live     |       9267 |           7 |
    | project-X | archived |          0 |           0 |
    | project-Y | live     |          0 |           0 |
    | project-Y | archived |          0 |           0 |
    +-----------+----------+------------+-------------+
                            +
    +-----------+----------+----------+-----------+
    |  project  |  state   | bam_size | bam_count |
    +-----------+----------+----------+-----------+
    | project-X | live     |     7691 |        29 |
    | project-X | archived |        0 |         0 |
    | project-Y | live     |        0 |         0 |
    | project-Y | archived |     2460 |         3 |
    +-----------+----------+----------+-----------+
                            +
    +-----------+----------+----------+-----------+
    |  project  |  state   | vcf_size | vcf_count |
    +-----------+----------+----------+-----------+
    | project-X | live     |    30019 |        52 |
    | project-X | archived |        0 |         0 |
    | project-Y | live     |        0 |         0 |
    | project-Y | archived |     1254 |         6 |
    +-----------+----------+----------+-----------+
                            |
                            ▼
    +-----------+-------------------+---------------+--------------------+
    |  project  | vcf_size_archived | vcf_size_live | vcf_count_archived |
    +-----------+-------------------+---------------+--------------------+
    | project-X |                 0 |         30019 |                  0 |
    | project-Y |              1254 |             0 |                  6 |
    +-----------+-------------------+---------------+--------------------+ ...
    +-----------+----------------+-------------------+---------------+
    |  project  | vcf_count_live | bam_size_archived | bam_size_live |
    +-----------+----------------+-------------------+---------------+
    | project-X |             52 |                 0 |          7691 |
    | project-Y |              0 |              2460 |             0 |
    +-----------+----------------+-------------------+---------------+ ...
    +-----------+--------------------+----------------+---------------------+
    |  project  | bam_count_archived | bam_count_live | fastq_size_archived |
    +-----------+--------------------+----------------+---------------------+
    | project-X |                  0 |            29  |                   0 |
    | project-Y |                  3 |              0 |                   0 |
    +-----------+--------------------+----------------+---------------------+..
    +-----------+-----------------+----------------------+------------------+
    |  project  | fastq_size_live | fastq_count_archived | fastq_count_live |
    +-----------+-----------------+----------------------+------------------+
    | project-X |            9267 |                    0 |                7 |
    | project-Y |               0 |                    0 |                0 |
    +-----------+-----------------+----------------------+------------------+

    """
    # Merge the three dfs together on project and state
    merged_file_df = reduce(
        lambda left, right: pd.merge(
            left,right,on=['project', 'state']
        ), list_of_aggregated_dataframes
    )

    # Convert from long format to wide based on project so one row per proj
    merged_file_df = merged_file_df.pivot(
        index='project', columns='state',
        values=[
            'vcf_size', 'vcf_count', 'bam_size',
            'bam_count', 'fastq_size', 'fastq_count'
        ]
    )

    # Rename the columns instead of being multiIndex
    merged_file_df.columns = merged_file_df.columns.map('_'.join)
    aggregated_all_file_types_df = merged_file_df.reset_index()

    return aggregated_all_file_types_df

def group_by_project_and_rename(df_name, string_to_replace):
    """
    Group the dataframe by project to get total size per file state
    Parameters
    ----------
    df_name : pd.DataFrame
        the dataframe you want to group (unique or total)
    string_to_replace : str
        'unique' or 'total'

    Returns
    -------
    grouped_df : pd.DataFrame
        dataframe grouped by project, state (e.g. total_live) which gives the aggregated size
    e.g.
    +-----------+-----------------+---------------+
    |  project  |      state      |     size      |
    +-----------+-----------------+---------------+
    | project-X | unique_live     | 1133796550572 |
    | project-X | unique_archived |         51238 |
    | project-Y | unique_live     |      58575459 |
    +-----------+-----------------+---------------+
    """
    # Group by project and file state and sum the size column to get total size (with duplicates)
    grouped_df = df_name.groupby(['project', 'state']).agg(
        size=('size', 'sum')).reset_index()

    # Replace the values with unique_ as it makes it easier to merge later
    grouped_df['state'] = grouped_df['state'].str.replace(
        'live', string_to_replace+"_live")
    grouped_df['state'] = grouped_df['state'].str.replace(
        'archived', string_to_replace+"_archived")

    return grouped_df

def calculate_totals(my_grouped_df, tot_or_uniq_type):
    """
    Calculate the total cost of storing per project
    by file state through rates defined in CREDENTIALS.json
    ----------
    my_grouped_df : pd.DataFrame
        the dataframe which is grouped by project
        and state with aggregated total size
    tot_or_uniq_type : str
        'unique' or 'total'

    Returns
    -------
    grouped_df : pd.DataFrame
        dataframe with calculated daily storage cost
        grouped by project and state with columns project, state, size, cost
    e.g.
    +-----------+-----------------+---------------+----------+
    |  project  |      state      |     size      |   cost   |
    +-----------+-----------------+---------------+----------+
    | project-X | unique_live     | 1133796550572 | 0.875400 |
    | project-X | unique_archived |         51238 | 0.011010 |
    | project-Y | unique_live     |      58575459 | 0.001498 |
    +-----------+-----------------+---------------+----------+
    """
    days_in_month = no_of_days_in_month()[1]
    # If the state of the file is live
    # Convert total size to GiB and times by storage cost per month
    # Then divide by the number of days in current month
    # Else if state not live (archived) then times by archived storage cost price

    my_grouped_df['cost'] = np.where(
        my_grouped_df['state'] == tot_or_uniq_type+"_live",
        my_grouped_df['size'] / (2**30) * settings.LIVE_STORAGE_COST_MONTH / days_in_month,
        my_grouped_df['size'] / (2**30) * settings.ARCHIVED_STORAGE_COST_MONTH / days_in_month)

    return my_grouped_df

def merge_together_add_empty_rows(df1, df2):
    """
    Merge two dataframes to make final dict and add zeros for file state
    categories which don't exist
    ----------
    df1 : pd.DataFrame
        the dataframe with costs for unique files per project
    type : str
        the dataframe with costs for all files per project

    Returns
    -------
    total_merged_df : pd.DataFrame
        merged dataframe with project, all file states (total_live, total_archived, unique_live, unique_archived),
        cost and size with zeros if did not exist
    e.g.
    +-----------+-----------------+---------------+----------+
    |  project  |      state      |     size      |   cost   |
    +-----------+-----------------+---------------+----------+
    | project-X | unique_live     | 1133796550572 | 0.875400 |
    | project-X | unique_archived |         51238 | 0.011010 |
    | project-X | total_live      | 1133796550572 | 0.875400 |
    | project-X | total_archived  |         71238 | 0.012038 |
    | project-Y | unique_live     |      58575459 | 0.001498 |
    | project-Y | unique_archived |             0 |        0 |
    | project-Y | total_live      |      68373901 | 0.004857 |
    | project-Y | total_archived  |             0 |        0 |
    +-----------+-----------------+---------------+----------+
    """
    # Merge the two together to have unique and total costs in one df
    total_merged_df = pd.concat([df1, df2], ignore_index=True, sort=True)

    # If there isn't a particular file state for a project
    # Add missing rows for each file state and set the size and cost to zero
    iterables = [total_merged_df['project'].unique(
    ), total_merged_df['state'].unique()]
    total_merged_df = total_merged_df.set_index(['project', 'state'])
    total_merged_df = total_merged_df.reindex(index=pd.MultiIndex.from_product(
        iterables, names=['project', 'state']), fill_value=0).reset_index()

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
        final df with proj, file state, total size+cost for all projects
    """
    # For the projects that were removed at the beginning because they are empty
    # Create a list of dictionaries with all the fields as zero
    empty_project_rows = []

    for proj in empty_projs:
        empty_project_rows.append(
            {'project': proj, 'state': 'total_live', 'cost': 0, 'size': 0})
        empty_project_rows.append(
            {'project': proj, 'state': 'total_archived', 'cost': 0, 'size': 0})
        empty_project_rows.append(
            {'project': proj, 'state': 'unique_live', 'cost': 0, 'size': 0})
        empty_project_rows.append(
            {'project': proj, 'state': 'unique_archived', 'cost': 0, 'size': 0})

    # Append the projects with no files to the final merged dataframe
    final_all_projs_df = total_merged_df.append(
        empty_project_rows, ignore_index=True, sort=False)

    return final_all_projs_df

def put_into_dict(final_all_projs_df):
    """
    Put back into a dict for easy adding to the db
    ----------
    final_all_projs_df : pd.DataFrame
        final dataframe with project, file state, total size and cost for all projects

    Returns
    -------
    all_proj_dict : dict
        final dictionary with key project and nested keys total_live, total_archived, unique_live, unique_archived
         (and nested size and cost within) for all projects
    e.g. {"project-XYZ": {
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
    all_proj_dict = {proj: state.loc[proj].to_dict('index') for proj, state in
                     final_all_projs_df.set_index(
                         ['project', 'state']).groupby(level='project')}

    return all_proj_dict

def get_analyses(proj):
    """
    Get all analyses for the project in DNAnexus,
    storing each file and its size, name and archival state.
    Used with ThreadExecutorPool

    Parameters
    ----------
    proj : project_id for the DNAnexus project

    Returns
    -------
     project_files_dict : collections.defaultdict
        dictionary with all the files per project

    """

    # Find analyses in each project, only returning specified fields in item
    project_analyses_dict = defaultdict(lambda: {"analysis": []})
    jobs = dx.bindings.search.find_executions(
            classname="analysis",
            project=proj,
            state="done",
            no_parent_analysis=True,
            created_after="-1d",
            describe=True
        )

    for job in jobs:
        proj = job['describe']['project']

        project_analyses_dict[proj]["analysis"].append({
                "id": job["id"],
                "name": job['describe']['name'],
                "cost": job['describe']['totalPrice'],
                "class": job['describe']['class'],
                "executable": job['describe']['executable'],
                "state": job['describe']['state'],
                "created": job['describe']['created'],
                "modified": job['describe']['modified'],
                "launchedBy": job['describe']['launchedBy'],
                "createdBy": job['describe']['workflow']['createdBy']
            })
    return project_analyses_dict


def make_analyses_df(list_project_analyses_dictionary):
    """
    Get all analyses from the list of analyses per proj dict
    and add it into a df.
    Parameters
    ----------
    list_project_analyses_dictionary: list of all analyses for each project.

    Returns
    -------
    list_of_project_analyses_dicts: list
        list of dictionaries for analyses for each project.
    """

    rows = []
    # For each project dictionary with its associated analyses
    for project_dict in list_project_analyses_dictionary:
        # For the project and its associated analyses
        for project, data in project_dict.items():
            # Get the analyses info
            data_row = data['analysis']

            # Add the project name to the row 'project'
            for row in data_row:
                row['project'] = project
                # Append each analyses info as info to the other columns
                rows.append(row)

    return pd.DataFrame(rows)



def orchestrate_get_files(proj_list, proj_df):
    """
    Orchestates all the functions for getting API data for files and returning
    only files with unique parent projects.
    paramaters
    ----------
    proj_list: list
        all the project IDs in a list
    proj_df: dataframe
        dataframe with a row for each project
    """
    project_file_dicts_list = threadify(proj_list)
    file_df = make_file_df(project_file_dicts_list)
    unique_without_empty_projs, empty_projs = count_how_many_lost(
        file_df, proj_list)
    merged_df = merge_files_and_proj_dfs(file_df, proj_df)
    unique_df = remove_duplicates(merged_df, unique_without_empty_projs)

    fastq_df = make_file_type_aggregate_df(unique_df, "fastq")
    vcf_df = make_file_type_aggregate_df(unique_df, "vcf")
    bam_df = make_file_type_aggregate_df(unique_df, "bam")

    fastq_final = add_missing_states_projects_file_types(
        file_df, fastq_df, 'fastq'
    )
    vcf_final = add_missing_states_projects_file_types(file_df, vcf_df, 'vcf')
    bam_final = add_missing_states_projects_file_types(file_df, bam_df, 'bam')

    file_type_df = generate_merged_file_df([vcf_final, bam_final, fastq_final])

    unique_grouped_df = group_by_project_and_rename(unique_df, 'unique')
    total_grouped_df = group_by_project_and_rename(merged_df, 'total')
    unique_sum_df = calculate_totals(unique_grouped_df, 'unique')
    total_sum_df = calculate_totals(total_grouped_df, 'total')
    merged_total_df = merge_together_add_empty_rows(
        unique_sum_df, total_sum_df
    )
    final_all_projs_df = add_empty_projs_back_in(empty_projs, merged_total_df)
    final_dict = put_into_dict(final_all_projs_df)

    return final_dict, file_type_df
