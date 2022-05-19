"""This script queries the DNAnexus API, puts this info into dictionaries and adds the data into four tables in the database"""

from django.core.management.base import BaseCommand, CommandError
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
from django.apps import apps
from django.conf import settings
from collections import defaultdict
import pandas as pd
import datetime as dt
import json
import dxpy as dx

class Command(BaseCommand):
    help = "Gets data from the API as dicts and puts it into the database."

    # Define org of interest from Django settings
    ORG = settings.ORG

    def handle(self, *args, **options):

        def login():
            """Log into DNAnexus using token defined in Django settings"""
            TOKEN = settings.DX_TOKEN
            DX_SECURITY_CONTEXT = {
            "auth_token_type": "Bearer",
            "auth_token": TOKEN
            }

            dx.set_security_context(DX_SECURITY_CONTEXT)

            try:
                dx.api.system_whoami()
            except:
                print("Error with DNAnexus login")

        def get_projects():
            """Get project data and put into a dictionary"""

            # Find all projs billed to org with view level and above, describe them all
            proj_list = list(dx.find_projects(billed_to=self.ORG, level='VIEW', describe=True))

            # Put each into dict, turn epoch time into datetime YYYY-MM-DD
            all_projects = defaultdict(dict)
            for project in proj_list:
                project_id = project['id']
                all_projects[project_id]['dx_id'] = project['describe']['id']
                all_projects[project_id]['name'] = project['describe']['name']
                all_projects[project_id]['created_by'] = project['describe']['createdBy']['user']
                created = dt.datetime.fromtimestamp((project['describe']['created']) / 1000).strftime('%Y-%m-%d')
                all_projects[project_id]['created'] = created

            # Reformat dict so each entry is one dictionary
            projects_dict = [value for value in all_projects.values()]

            #Make json dump for debugging
            json_obj = json.dumps(projects_dict, indent=4)
            with open("project_data.json", "w") as outfile:
                outfile.write(json_obj)

            return projects_dict

        def get_running_totals():
            """Get the running totals from the API"""

            # Get today's date in YYY-MM-DD format
            today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/","-")

            # Describe the org to get running totals
            org = dx.api.org_describe(self.ORG)

            # Put values into dict
            running_total_dict = {}
            running_total_dict['storage_charges'] = org['storageCharges']
            running_total_dict['compute_charges'] = org['computeCharges']
            running_total_dict['egress_charges'] = org['dataEgressCharges']
            running_total_dict['estimated_balance'] = org['estSpendingLimitLeft']
            running_total_dict['date'] = today_date
            
            return running_total_dict
        
        def populate_projects():
            """Add the projects into the db"""
            # In case project names have been changed in DX
            # Get all project objects in db to filter on later
            projects_data = Projects.objects.all()

            # Get all projects data from DNAnexus
            all_projects = get_projects()

            # Iterate over dict and add to db
            for entry in all_projects:
                # Add users to users table to create IDs
                user, created = Users.objects.get_or_create(
                    user_name = entry['created_by'],
                )

                # Add project created dates to Dates table to create IDs
                a_new_date, created = Dates.objects.get_or_create(
                    date = entry['created'],
                )

                # Get names of projects from our dict
                new_name = entry['name']

                # Dict to filter on
                filter_dict = {
                    "dx_id": entry['dx_id'],
                }

                # Filter the projects
                found_entry = projects_data.filter(**filter_dict)

                # If already in db, get the name
                if found_entry:
                    existing_project = found_entry.values_list(
                        "name", flat=True
                    ).get()
                
                    if existing_project != new_name:
                        found_entry.update(name=new_name)
                
                # Get or create objs in Projects with attributes from other tables
                project, created = Projects.objects.get_or_create(
                    dx_id = entry['dx_id'],
                    name = entry['name'],
                    created_by = user,
                    created = a_new_date,
                )
        
        def populate_running_total():
            """Add the running totals into the db"""
            # Create dict with previous function
            running_tots_dict = get_running_totals()
                
            # Make date entry
            new_date, created = Dates.objects.get_or_create(
                date = running_tots_dict['date'],
            )

            # Add running totals to totals table with date foreign key
            total, created = DailyOrgRunningTotal.objects.get_or_create(
                date = new_date,
                storage_charges = running_tots_dict['storage_charges'],
                compute_charges = running_tots_dict['compute_charges'],
                egress_charges = running_tots_dict['egress_charges'],
                estimated_balance = running_tots_dict['estimated_balance'],
            )


        login()
        populate_projects()
        populate_running_total()

