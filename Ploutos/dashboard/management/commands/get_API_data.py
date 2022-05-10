from django.core.management.base import BaseCommand, CommandError
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
from django.apps import apps
import pandas as pd
import itertools
from collections import UserString
from collections import defaultdict, Counter
import os
import sys
import requests
import json
import dxpy as dx
import datetime as dt
from pathlib import Path

class Command(BaseCommand):
    help = "Gets data from the API and puts it into csvs."

    def handle(self, *args, **options):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        # Get auth token from separate file
        with open(f"{BASE_DIR}/Ploutos/Ploutos/auth_token.json") as token_file:
            CREDENTIALS = json.load(token_file)

        TOKEN = CREDENTIALS['DNANEXUS_TOKEN']

        ORG = 'org-emee_1'

        # Get date in YYY-MM-DD format
        today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/","-")

        # Give context the token
        DX_SECURITY_CONTEXT = {
            "auth_token_type": "Bearer",
            "auth_token": TOKEN
        }

        dx.set_security_context(DX_SECURITY_CONTEXT)

        # Search all projs billed to org, including access level view and above
        proj_list = list(dx.find_projects(billed_to=ORG, level='VIEW', describe=True))

        # Make dict of projects
        # Turn created epoch time into correct dateform
        all_projects = defaultdict(dict)
        for project in proj_list:
            project_id = project['id']
            all_projects[project_id]['dx_id'] = project['describe']['id']
            all_projects[project_id]['name'] = project['describe']['name']
            all_projects[project_id]['created_by'] = project['describe']['createdBy']['user']
            created = dt.datetime.fromtimestamp((project['describe']['created']) / 1000).strftime('%Y-%m-%d')
            all_projects[project_id]['created'] = created

        # Transform into pandas df
        projects_df = pd.DataFrame.from_dict(all_projects.values())

        # Save as csv in main dir
        projects_df.to_csv(f'{BASE_DIR}/projects.csv',sep='\t', index=False)

        # Running totals
        org = dx.api.org_describe(ORG)

        # Put values into dict
        running_total_dict = {}
        running_total_dict['storage_charges'] = org['storageCharges']
        running_total_dict['compute_charges'] = org['computeCharges']
        running_total_dict['egress_charges'] = org['dataEgressCharges']
        running_total_dict['estimated_balance'] = org['estSpendingLimitLeft']
        running_total_dict['date'] = today_date

        # Reformat dict to put into df
        reformat_running_tot = {k: [v] for k, v in running_total_dict.items()}

        # Create df
        running_total_df = pd.DataFrame.from_dict(reformat_running_tot)

        # Save as csv in main dir
        running_total_df.to_csv(f'{BASE_DIR}/running_totals.csv', sep="\t",index=False)



