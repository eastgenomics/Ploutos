"""
    Script to add data to MariaDB.
"""

from dashboard.models import ComputeCosts, Users, Dates, Projects, Executables
from scripts import queries as q
from scripts import queries_jobs as qa
from scripts import API_queries_populate as apq
import datetime as dt

from calendar import monthrange
from collections import defaultdict
from django.apps import apps
from django.conf import settings
from time import time, localtime, strftime
import pandas as pd


def populate_projects():
    """
    Populate database with data from API query.
    Summary:
    This function requests all projects in given ORG and populates the tables.
    - This is to be merged with populate_projects() in API_queries_populate.py

    """

    # all_data_objs = q.find_all_data_objs()
    all_projects = apq.get_projects()
    for project in all_projects:
        project_dict = project.describe()
        # print(project_dict)
        # Adding Users to table
        user, created = Users.objects.get_or_create(
            user_name=project_dict['createdBy']['user'],)

        # Adding dates to table
        a_new_date, created = Dates.objects.get_or_create(
            date=dt.datetime.fromtimestamp(
                project_dict['created']/1000).strftime('%Y-%m-%d'),)

        # Adding project details to table
        # update_or_create allows for changes in project data.
        project, created = Projects.objects.update_or_create(
            dx_id=project_dict['id'],
            name=project_dict['name'],
            created_by=user,
            created=a_new_date,
        )
    return all_projects


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
        #print(proj)
        analyses = qa.get_analyses(proj['dx_id'])
        all_analyses.append(analyses)
    all_analyses_df = qa.make_analyses_df(all_analyses)

    for index, row in all_analyses_df.iterrows():
        print(row)
        print("---\n")

        #Add date for analysis started.
        a_new_date, created = Dates.objects.get_or_create(
            date=dt.datetime.fromtimestamp(
                (int(row['created'])) / 1000).strftime('%Y-%m-%d')
        )

        # Add data to DB - Executables Table
        new_analysis, created = Executables.objects.get_or_create(
            dx_id=row['executable'],
            excutable_name=row['name']
        )

        #Add date for analysis started.
        user, created = Users.objects.get_or_create(
            user_name=row['launchedBy'],)
        print(user)
        # Add data to DB - ComputeCosts Table
        new_analysis_costs, created = ComputeCosts.objects.get_or_create(
            # Get the project ID from the projects table by project dx id
            # project=Projects.objects.get(dx_id=key),
            executable_id=new_analysis,
            project_id=Projects.objects.get(dx_id=row['project']),
            # instance_id = row['']
            # runtime = row['']
            total_cost = row['cost'],
            launched_by=user,
            date_id=a_new_date
        )
        print("done")
        # # Get date object from the dates table
        # #date=Dates.objects.get(date=today_date),


def run():
    """
    Main function to orchestrate population of the database with API data.
    """

    q.DNAnexus_login()
    all_projects, proj_list, proj_df = apq.get_projects()
    apq.populate_projects(all_projects)
    populate_analyses(all_projects)
