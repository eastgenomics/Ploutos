"""
    Script to add API data to MariaDB Database.
"""
import datetime as dt
from http.server import executable
import pandas as pd

import dxpy as dx

from calendar import monthrange
from collections import defaultdict
from time import time, localtime, strftime

from django.apps import apps
from django.conf import settings
from dashboard.models import ComputeCosts, DailyOrgRunningTotal, Executables, Users, Dates, Projects, StorageCosts
from scripts import DNAnexus_queries as queries


def populate_projects(all_projects) -> None:
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


def populate_running_totals() -> None:
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
    today_date = queries.no_of_days_in_month()[0]

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


def populate_database_files(all_projects_dict) -> None:
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

    today_date = queries.no_of_days_in_month()[0]

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


def populate_executions(all_executions_df) -> None:
    """
    Populate database with data from API query.
    This function iterates over all projects and returns all parent executions
    that have finished in the last 24 hrs.
    It then populates the database with this data.

    --- This is still in development with the models.py ---

    Parameters
    ----------
    all_executions_df:
        dataframe with all parent executions run in timeperiod specified.
    Returns
    -------
    None

    """

    for index, row in all_executions_df.iterrows():
        print(row)
        print("---\n")

        # Add date for analysis started.
        date = dt.datetime.fromtimestamp(row['created'] / 1000)
        date_formatted = date.strftime("%Y-%m-%d")
        a_new_date, created = Dates.objects.get_or_create(
            date=date_formatted,)

        # Add date for analysis started.
        user, created = Users.objects.get_or_create(
            user_name=row['launchedBy'],)

        # Add executable name to table
        new_executable, created = Executables.objects.get_or_create(
            # Get the project ID from the projects table by project dx id
            executable_name=row['executable_name']
        )

        # Add data to DB - ComputeCosts Table
        new_analysis_costs, created = ComputeCosts.objects.get_or_create(
            # Get the project ID from the projects table by project dx id
            dx_id=row['id'],
            #job_name=row['job_name'],
            executable_name=new_executable,
            project=Projects.objects.get(dx_id=row['project']),
            runtime=row['Result'],
            total_cost=row['cost'],
            state=row['state'],
            launched_by=user,
            date=a_new_date,
        )


def run():
    """
    Main function to orchestrate population of the database with API data.
    """
    start = time()
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))

    queries.login()
    all_projects, proj_list, proj_df = queries.get_projects()
    populate_projects(all_projects)
    # populate_running_totals()
    # final_dict = queries.orchestrate_get_files(proj_list, proj_df)
    # populate_database_files(final_dict)
    executions_df = queries.orchestrate_get_executions(proj_list)
    print(executions_df)
    populate_executions(executions_df)
    end = time()
    total = (end - start) / 60
    print(f"Total time was {total} minutes")
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()))
