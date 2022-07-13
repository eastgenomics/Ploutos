"""
    Script to add API data to MariaDB Database.
"""
import datetime as dt
import pandas as pd
import dxpy as dx

from calendar import monthrange
from collections import defaultdict
from time import time, localtime, strftime

from django.apps import apps
from django.conf import settings
from dashboard.models import DailyOrgRunningTotal, Users, Dates, Projects, StorageCosts, FileTypeDate, FileTypes, FileTypeState
from scripts import DNAnexus_queries as q


def populate_projects(all_projects):
    """
    Checks whether user exists or creates it to get ID
    Checks whether date exists or creates it to get ID
    Checks whether project exists already and updates name if needed
    Adds data into the Projects table

    """
    # In case project names have been changed in DX
    # Get all project objects in db to filter on later
    # Update_or_create wasn't working so this does for now
    projects_data = Projects.objects.all()

    # Iterate over list of project dicts
    for entry in all_projects:
        # Add users to users table to create IDs
        user, created = Users.objects.get_or_create(
            user_name=entry['created_by'],
        )

        # Add project created dates to Dates table to create or get IDs
        new_date, created = Dates.objects.get_or_create(
            date=entry['created'],
        )

        # Get names of projects from our dict
        new_name = entry['name']

        # Dict to filter on dx_id
        filter_dict = {
            "dx_id": entry['dx_id'],
        }

        # Filter the projects to see if dx_id already exists
        found_entry = projects_data.filter(**filter_dict)

        # If already in db, get the name
        if found_entry:
            existing_project = found_entry.values_list(
                "name", flat=True
            ).get()

            if existing_project != new_name:
                found_entry.update(name=new_name)

        # Get or create objs in Projects with attributes from other tables
        project, created = Projects.objects.update_or_create(
            dx_id=entry['dx_id'],
            name=entry['name'],
            created_by=user,
            created=new_date,
        )


def populate_running_totals():
    """
    Adds org running totals into the db, getting the date IDs or creating them first
    """

    # Get today's date in YYY-MM-DD format
    today_date = q.no_of_days_in_month()[0]

    # Describe the org to get running totals
    org_totals = dx.api.org_describe(settings.ORG)

    # Make date entry
    new_date, created = Dates.objects.get_or_create(
        date=today_date,
    )

    # Add running totals to totals table with date foreign key
    total, created = DailyOrgRunningTotal.objects.get_or_create(
        date=new_date,
        storage_charges=org_totals['storageCharges'],
        compute_charges=org_totals['computeCharges'],
        egress_charges=org_totals['dataEgressCharges'],
        estimated_balance=org_totals['estSpendingLimitLeft'],
    )


def populate_database_files(all_projects_dict):
    """
    Puts the storage data into the db
    ----------
    all_projects_dict : dict
        final dictionary from put_into_dict_write_to_file function

    Returns
    -------
    none
    """

    today_date = q.no_of_days_in_month()[0]

    for key, value in all_projects_dict.items():
        new_storage, created = StorageCosts.objects.get_or_create(
            # Get project ID from the projects table by project dx_id
            project=Projects.objects.get(dx_id=key),
            unique_size_live=value['unique_live']['size'],
            unique_cost_live=value['unique_live']['cost'],
            unique_size_archived=value['unique_archived']['size'],
            unique_cost_archived=value['unique_archived']['cost'],

            total_size_live=value['total_live']['size'],
            total_cost_live=value['total_live']['cost'],
            total_size_archived=value['total_archived']['size'],
            total_cost_archived=value['total_archived']['cost'],
            # Get date object from the dates table
            date=Dates.objects.get(date=today_date),
        )

def populate_file_types(file_type_df):
    """
    Puts the file type data into the db
    ----------
    file_type_df : pd.DataFrame
        dataframe with one row per project and all the file types
        and their sizes + counts (live + archived)

    Returns
    -------
    None
    """
    # Convert to dict with projects as keys, counts + sizes as vals
    file_types_dict = file_type_df.set_index("project").to_dict("index")
    today_date = q.no_of_days_in_month()[0]

    for project, file_vals in file_types_dict.items():
        # Add in or get the file type
        new_file_type, created = FileTypes.objects.get_or_create(
            file_type='vcf'
        )

        # If the state exists, get it, or create new state id
        state, created = FileTypeState.objects.get_or_create(
            file_type = new_file_type,
            file_count_live = file_vals['vcf_count_live'],
            file_count_archived = file_vals['vcf_count_archived'],
            file_size_live = file_vals['vcf_size_live'],
            file_size_archived = file_vals['vcf_size_archived']
        )

        # Add the proj, date and state to the FileTypeDate table
        object, created = FileTypeDate.objects.get_or_create(
            project = Projects.objects.get(dx_id=project),
            date = Dates.objects.get(date=today_date),
            file_state = state
        )

        # Do same for BAMs
        new_file_type, created = FileTypes.objects.get_or_create(
            file_type='bam'
        )

        state, created = FileTypeState.objects.get_or_create(
            file_type = new_file_type,
            file_count_live = file_vals['bam_count_live'],
            file_count_archived = file_vals['bam_count_archived'],
            file_size_live = file_vals['bam_size_live'],
            file_size_archived = file_vals['bam_size_archived']
        )

        object, created = FileTypeDate.objects.get_or_create(
            project = Projects.objects.get(dx_id=project),
            date = Dates.objects.get(date=today_date),
            file_state = state
        )

        # Do same for FASTQs
        new_file_type, created = FileTypes.objects.get_or_create(
            file_type='fastq'
        )

        state, created = FileTypeState.objects.get_or_create(
            file_type = new_file_type,
            file_count_live = file_vals['fastq_count_live'],
            file_count_archived = file_vals['fastq_count_archived'],
            file_size_live = file_vals['fastq_size_live'],
            file_size_archived = file_vals['fastq_size_archived'],
        )

        object, created = FileTypeDate.objects.get_or_create(
            project = Projects.objects.get(dx_id=project),
            date = Dates.objects.get(date=today_date),
            file_state = state
        )

# def populate_analyses(all_projects):
#     """
#     Populate database with data from API query.
#     This function iterates over all projects and returns all parent executions
#     that have finished in the last 24 hrs.
#     It then populates the database with this data.

#     --- This is still in development with the models.py ---

#     Parameters
#     ----------
#     all_projects: list of all projects in the DNAnexus ORG.

#     Returns
#     -------
#     None
#     """
#     all_analyses = []
#     for proj in all_projects:
#         #print(proj)
#         analyses = q.get_analyses(proj['dx_id'])
#         all_analyses.append(analyses)
#     all_analyses_df = q.make_analyses_df(all_analyses)

#     for index, row in all_analyses_df.iterrows():
#         print(row)
#         print("---\n")

#         #Add date for analysis started.
#         a_new_date, created = Dates.objects.get_or_create(
#             date=dt.datetime.fromtimestamp(
#                 (int(row['created'])) / 1000).strftime('%Y-%m-%d')
#         )

#         # Add data to DB - Executables Table
#         project_row_id = Projects.objects.get(dx_id=row['project'])
#         project_row_id = project_row_id.values()
#         new_analysis, created = Executables.objects.get_or_create(
#             dx_id=row['executable'],
#             excutable_name=row['name'],
#             project_id=project_row_id['project']
#         )
#         #Add date for analysis started.
#         user, created = Users.objects.get_or_create(
#             user_name=row['launchedBy'],)
#         print(user)
#         # Add data to DB - ComputeCosts Table
#         new_analysis_costs, created = ComputeCosts.objects.get_or_create(
#             # Get the project ID from the projects table by project dx id
#             # project=Projects.objects.get(dx_id=key),
#             executable_id=new_analysis,
#             # instance_id = row['']
#             # runtime = row['']
#             total_cost = row['cost'],
#             launched_by=user,
#             date_id=a_new_date
#         )
#         print("done")


def run():
    """
    Main function to orchestrate population of the database with API data.
    """
    start = time()
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))

    q.login()
    all_projects, proj_list, proj_df = q.get_projects()
    print("Populating projects")
    populate_projects(all_projects)
    populate_running_totals()
    print("Getting files")
    final_dict, file_type_df = q.orchestrate_get_files(proj_list, proj_df)
    print("Putting file stuff in db")
    populate_database_files(final_dict)
    populate_file_types(file_type_df)
    # populate_analyses(all_projects)
    end = time()
    total = (end - start) / 60
    print(f"Total time was {total} minutes")
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))
