"""This script is testing queries for file searching in DNAnexus
It currently gets all files in DNAnexus, puts info into a dict grouped by project, 
then sums size values per project for live/archival and archived files and saves it to a json"""
import datetime as dt
import json
import pandas as pd
import time
import dxpy as dx

from calendar import monthrange
from collections import defaultdict
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Gets file info from the API and calculates storage costs."

    # Define org of interest
    ORG = settings.ORG

    today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/","-")
    year, month = int(today_date.split("-")[0]), int(today_date.split("-")[1])

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
                print("DNAnexus login successful")
            except:
                print("Error with DNAnexus login")

        def no_of_days_in_month(year, month):
            """Get the number of days in a month by the year and month"""
            return monthrange(year, month)[1]

        def find_duplicates(file_ids):
            """Finds duplicates from a list of file IDs"""
            seen = set()
            seen_add = seen.add
            # Add all elements it doesn't know yet to seen and all others to seen_twice
            seen_twice = set(x for x in file_ids if x in seen or seen_add(x))
            return list(seen_twice)

        def get_projects():
            """Get all projects in DNAnexus"""
            project_response = list(dx.find_projects(billed_to='org-emee_1', level='VIEW', describe=True))

            project_ids_list = []

            all_projects = defaultdict(dict)
            for project in project_response:
                project_id = project['id']
                project_ids_list.append(project_id)
                all_projects[project_id]['dx_id'] = project['describe']['id']
                all_projects[project_id]['name'] = project['describe']['name']
                all_projects[project_id]['created_by'] = project['describe']['createdBy']['user']
                all_projects[project_id]['created_epoch'] = project['describe']['created']
                all_projects[project_id]['created'] = dt.datetime.fromtimestamp((project['describe']['created']) / 1000).strftime('%Y-%m-%d')
            return all_projects, project_ids_list


        def get_files():
            """Gets files per proj and their info and puts into a nested dict"""
            project_list = get_projects()[1]
            print("Starting to look for all files in DNAnexus")
            start = time.time()

            files_per_proj_dict = defaultdict(lambda: {"files": []})
            for proj in project_list:
                files = list(dx.search.find_data_objects(classname='file', project = proj, describe={'fields':{'archivalState': True, 'size': True, 'name': True}}))
                for file in files:
                    #file_id_list.append(d['id'])
                    proj = file['project']
                    files_per_proj_dict[proj]["files"].append({"id": file["id"], "name": file["describe"]['name'], "size": file.get('describe',{}).get('size',0), "state": file['describe']['archivalState']})

            end = time.time()
            total_time = end - start
            print(f"Total time to get all files was {total_time}")

            return files_per_proj_dict

        def calculate_total():
            """Calculates total cost per project (not taking into account duplicates) currently"""
            # Cost per GB per month from DNAnexus
            live_storage_cost_month = settings.STORAGE_COST_MONTH
            # This is an arbitrary number until Wook provides it
            archived_storage_cost_month = 0.0014

            # Find days in month to work out daily charge
            days_in_month = no_of_days_in_month(self.year, self.month)
            today_date = self.today_date

            # Get the files into a dict
            files_per_proj_dict = get_files()

            # For each project, total the sizes of the files 
            # Then convert to GB, multiply by cost per month and divide by days in month to get daily charge estimate

            files_dict = {}
            list_of_files_dicts = []
            for k, v in files_per_proj_dict.items():
                total_size_live = sum([x['size'] for x in v['files'] if x['state'] == "live"])
                total_size_archived = sum([x['size'] for x in v['files'] if x['state'] != "live"])
                total_cost_live = (((total_size_live / (2**30)) * live_storage_cost_month) / days_in_month)
                total_cost_archived = (((total_size_archived / (2**30)) * archived_storage_cost_month) / days_in_month)

                files_dict = {"project": k, "total_size_live": total_size_live, "total_size_archived": total_size_archived, 
                            "total_cost_live": total_cost_live, "total_cost_archived": total_cost_archived, 'date':today_date}

                list_of_files_dicts.append(files_dict)

            return list_of_files_dicts

        def jsonify():
            files_dicts = calculate_total()
            files_totals = json.dumps(files_dicts,indent=4)
            with open("files_proj_totals.json", "w") as outfile:
                outfile.write(files_totals)
                
        start=time.time()
        login()
        get_files()
        jsonify()
        end=time.time()
        total = end - start
        print(f"Total time was {total} seconds")