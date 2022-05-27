"""
This script gets all analyses from DNAnexus into a dict grouped by project,
then inserts all analyses into a df to calculates total cost.
It will have a 24-48hr lag to allow for jobs to finish so cost is not calculated
until it has finished.
This can then be imported and used with populate_db.py to insert data into the DB.

Changes to make:
- Combine functions across queries to make them generic and pass in args.
- One script for queries and one for populating DB which imports queries.
"""

#import concurrent.futures
import datetime as dt
# import json
import numpy as np
import pandas as pd
import sys
import dxpy as dx

from calendar import monthrange
from collections import defaultdict
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal, StorageCosts
from django.apps import apps
from django.conf import settings
from time import time, localtime, strftime


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
        Prints "DNAnexus login successful" or "Error with DNAnexus login".
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
    projects_ids_list : list
        all the project IDs in a list
    projects_df : pd.DataFrame
        dataframe with a row for each project
    """
    project_response = list(dx.find_projects(
        billed_to=settings.ORG, level='VIEW', describe=True))

    project_ids_list = []

    all_projects = defaultdict(dict)
    for project in project_response:
        project_id = project['id']
        project_ids_list.append(project_id)
        all_projects[project_id]['project'] = project['describe']['id']
        all_projects[project_id]['created_epoch'] = project['describe']['created']

    # Create a df with a row for each project from the dict
    projects_df = pd.DataFrame.from_dict(all_projects.values())

    return all_projects, project_ids_list, projects_df




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

    Example data (rm or shorten for production):
    {'id': 'stage-Fyq5yy0433GXxz691bKyvjPJ',
     'execution': {'id': 'job-GB3kx704vyJ7Yj3v0V66YgK5',
     'region': 'aws:eu-central-1', 'name': 'generate_bed_for_athena',
     'tags': [], 'properties': {}, 'executable': 'app-G9PG14j4FX73bqGK5VQ2qjkb',
     'executableName': 'generate_bed', 'class': 'job', 'created': 1653055131994,
     'modified': 1653055392933, 'project': 'project-G9G1jPQ4vyJ0j6075Qpq9GkK',
     'billTo': 'org-emee_1',
     'costLimit': None,
     'invoiceMetadata': None, 'folder': '/output/dias_single_v1.3.0-TWE_v1.0.7-220308-1/dias_reports_v2.0.0-TWE_v1.0.9-220520-2/generate_bed',
     'parentJob': None,
     'originJob': 'job-GB3kx704vyJ7Yj3v0V66YgK5',
     'parentAnalysis': 'analysis-GB3kx6j4vyJ7Yj3v0V66YgJz',
     'analysis': 'analysis-GB3kx6j4vyJ7Yj3v0V66YgJz',
     'stage': 'stage-Fyq5yy0433GXxz691bKyvjPJ',
     'rootExecution': 'analysis-GB3kx6j4vyJ7Yj3v0V66YgJz',
     'state': 'done', 'function': 'main',
     'workspace': 'container-GB3kx8Q4fzq3V784PxVZ736z',
     'launchedBy': 'user-ykim', 'detachedFrom': None,
     'priority': 'normal',
     'workerReuseDeadlineRunTime': {'state': 'reuse-off', 'waitTime': -1, 'at': -1},
     'dependsOn': [], 'failureCounts': {},
     'stateTransitions': [{'newState': 'runnable', 'setAt': 1653055138592},
     {'newState': 'running', 'setAt': 1653055340836},
     {'newState': 'done', 'setAt': 1653055389595}],
     'singleContext': False, 'ignoreReuse': False,
     'httpsApp': {'enabled': False}, 'rank': 0, 'details': {},
     'systemRequirements': {'*': {'instanceType': 'mem1_ssd1_v2_x4'}},
     'executionPolicy': {'restartOn': {'UnresponsiveWorker': 2, 'JMInternalError': 1,
     'ExecutionError': 1}}, 'instanceType': 'mem1_ssd1_v2_x4', 'finalPriority': 'normal',
     'networkAccess': [],
     'debug': {}, 'app': 'app-G9PG14j4FX73bqGK5VQ2qjkb',
     'resources': 'container-G9PG14j4yKP3bqGK5VQ2qjkf',
     'projectCache': 'container-GB351yj4vyJ1kg2f4JkBP1qp',
     'startedRunning': 1653055340836, 'stoppedRunning': 1653055386456,
     'delayWorkspaceDestruction': False, 'isFree': False,
     'totalPrice': 0.0034468444444444445,
     'totalEgress': {'regionLocalEgress': 0, 'internetEgress': 0, 'interRegionEgress': 0},
     'egressComputedAt': 1653055392889, 'priceComputedAt': 1653055392889,
     'currency': {'dxCode': 0, 'code': 'USD', 'symbol': '$', 'symbolPosition': 'left', 'decimalSymbol': '.', 'groupingSymbol': ','},
     'egressReport': {'regionLocalEgress': 0, 'internetEgress': 0, 'interRegionEgress': 0}, 'timeout': 3600000}}

    """

    # Find analyses in each project, only returning specified fields in item
    project_analyses_dict = defaultdict(lambda: {"analysis": []})
    jobs = dx.bindings.search.find_executions(classname="analysis",
                                              project=proj,
                                              state="done",
                                              # no_parent_job=False,
                                              # parent_analysis="null",
                                              no_parent_analysis=True,
                                              # root_execution=None,
                                              created_after="-1d",
                                              # created_before="-1d",
                                              describe=True)

    # jobs = list(dx.search.find_data_objects(classname='analyses', project=proj, describe={
    #     'fields': {'archivalState': True, 'size': True, 'name': True}}))
    for job in jobs:
        proj = job['describe']['project']
        # print(job)
        # item = {"id": job["id"],
        #         "name": job['describe']['name'],
        #         "cost": job['describe']['totalPrice'],
        #         "class": job['describe']['class'],
        #         "executable": job['describe']['executable'],
        #         # "totalEgress": job['describe']['totalEgress'],
        #         "state": job['describe']['state'],
        #         "created": job['describe']['created'],
        #         "launchedBy": job['describe']['launchedBy'],
        #         "WorkflowID": job['describe']['workflow']['id'],
        #         "createdBy": job['describe']['workflow']['createdBy'],
        #         }
        #print(job)

        project_analyses_dict[proj]["analysis"].append({"id": job["id"],
                "name": job['describe']['name'],
                "cost": job['describe']['totalPrice'],
                "class": job['describe']['class'],
                "executable": job['describe']['executable'],
                # "totalEgress": job['describe']['totalEgress'],
                "state": job['describe']['state'],
                "created": job['describe']['created'],
                "modified": job['describe']['modified'],
                "launchedBy": job['describe']['launchedBy'],
                #"WorkflowID": job['describe']['workflow']['id'],
                #'startedRunning': job['describe']['startedRunning'],
                #'stoppedRunning': job['describe']['stoppedRunning'],
                "createdBy": job['describe']['workflow']['createdBy']})
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
    # For each project dictionary with its associated files
    for project_dict in list_project_analyses_dictionary:
        # For the project and its associated files
        for k, v in project_dict.items():
            # Get the file info
            data_row = v['analysis']
            # Assign the project as the parent key
            project = k

            # Add the project name to the row 'project'
            for row in data_row:
                row['project'] = project
                # Append each file's info as info to the other columns
                rows.append(row)

    # Convert to data frame
    analysis_df = pd.DataFrame(rows)

    # sum_column = (
    #     (analysis_df["stoppedRunning"] + analysis_df["startedRunning"])/60
    #     )
    # analysis_df["RunTime"] = sum_column

    return analysis_df


def run():
    "Main function for script"
    # start = time()
    # print(strftime("%Y-%m-%d %H:%M:%S", localtime()))

    login(settings.DX_TOKEN)
    # all_projects, proj_list, proj_df = get_projects()
    # all_analyses = []
    # for proj in proj_list:
    #     analyses = get_analyses(proj)
    #     all_analyses.append(analyses)
    # df = make_file_df(all_analyses)

    # end = time()
    # total = (end - start) / 60
    # print(f"Total time was {total} minutes")
    # print(strftime("%Y-%m-%d %H:%M:%S", localtime()))
