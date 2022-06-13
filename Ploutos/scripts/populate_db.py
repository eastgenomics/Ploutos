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
from dashboard.models import ComputeCosts, DailyOrgRunningTotal, Users, Dates, Projects, Executables, StorageCosts
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
    # projects_data = Projects.objects.all()

    # Iterate over list of project dicts
    for entry in all_projects:
        # Add users to users table to create IDs
        user, created = Users.objects.get_or_create(
            user_name=entry['created_by'],
        )

        # Add project created dates to Dates table to create IDs
        a_new_date, created = Dates.objects.get_or_create(
            date=entry['created'],
        )

        # Get or create objs in Projects with attributes from other tables
        project, created = Projects.objects.update_or_create(
            dx_id=entry['dx_id'],
            name=entry['name'],
            created_by=user,
            created=a_new_date,
        )


def populate_running_totals():
    """
    populate_running_totals():

    Populates the database with data
    from API query for organisation level costs.
    The organisation ID is set in config file (CREDENTIALS.json).

    Adds org running totals into the db,
    getting the date IDs or creating them first.

    Parameters
    ----------
    None

    Returns
    -------
    None
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
        storage_charges=org_totals['storage_charges'],
        compute_charges=org_totals['compute_charges'],
        egress_charges=org_totals['egress_charges'],
        estimated_balance=org_totals['estimated_balance'],
    )


def populate_database_files(all_projects_dict):
    """
    Puts the file storage data into the db.
    Parameters
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
            # Get the project ID from the projects table by project dx id
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
            date=Dates.objects.get_or_create(date=today_date),
        )


def populate_analyses(all_projects):
    """
    Populate database with data from API query.
    This function iterates over all projects and returns all parent executions
    that have finished in the last 24 hrs.
    It then populates the database with this data.

    --- This is still in development with the models.py ---

    Parameters
    ----------
    all_projects: list of all projects in the DNAnexus ORG.

    Returns
    -------
    None
    """
    all_analyses = []
    for proj in all_projects:
        analyses = q.get_analyses(proj['dx_id'])
        all_analyses.append(analyses)
    all_analyses_df = q.make_analyses_df(all_analyses)

    for index, row in all_analyses_df.iterrows():
        print(row)
        print("---\n")

        # Add date for analysis started.
        a_new_date, created = Dates.objects.get_or_create(
            date=dt.datetime.fromtimestamp(
                (int(row['created'])) / 1000).strftime('%Y-%m-%d')
        )

        # Add data to DB - Executables Table
        project_row_id = Projects.objects.get(dx_id=row['project'])
        project_row_id = project_row_id.values()
        new_analysis, created = Executables.objects.get_or_create(
            dx_id=row['executable'],
            excutable_name=row['name'],
            project_id=project_row_id['project']
        )
        # Add date for analysis started.
        user, created = Users.objects.get_or_create(
            user_name=row['launchedBy'],)
        print(user)
        # Add data to DB - ComputeCosts Table
        new_analysis_costs, created = ComputeCosts.objects.get_or_create(
            # Get the project ID from the projects table by project dx id
            # project=Projects.objects.get(dx_id=key),
            executable_id=new_analysis,
            # instance_id = row['']
            # runtime = row['']
            total_cost = row['cost'],
            launched_by=user,
            date_id=a_new_date
        )
        print("done")


def run():
    """
    Main function to orchestrate population of the database with API data.
    """
    start = time()
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))

    q.login()
    all_projects, proj_list, proj_df = q.get_projects()
    populate_projects(all_projects)
    populate_running_totals()
    final_dict = q.orchestrate_get_files(proj_list, proj_df)
    populate_database_files(final_dict)
    # populate_analyses(all_projects)
    end = time()
    total = (end - start) / 60
    print(f"Total time was {total} minutes")
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))
