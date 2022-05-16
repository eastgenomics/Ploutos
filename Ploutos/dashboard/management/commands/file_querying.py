"""This script is testing queries for file searching in DNAnexus
It currently gets all file IDs in DNAnexus, works out which are duplicates (in multiple projects)
It then loops over each project to calculate total size of non-duplicate live and archived files and adds this to a dict which is saved to a json"""

from django.core.management.base import BaseCommand, CommandError
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
from django.apps import apps
from django.conf import settings
from collections import defaultdict
import pandas as pd
import datetime as dt
from collections import defaultdict
import time
import json
import dxpy as dx
from calendar import monthrange

class Command(BaseCommand):
    help = "Gets data from the API as dicts and puts it into the database."

    # Define org of interest
    ORG = 'org-emee_1'

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

        def no_of_days_in_month(year, month):
            """Get the number of days in a month by the year and month"""
            return monthrange(year, month)[1]

        def find_duplicates(file_ids):
            """Finds duplicates from a list of file IDs"""
            seen = set()
            seen_add = seen.add
            # Add all elements it doesn't know yet to seen and all others to seen_twice
            seen_twice = set( x for x in file_ids if x in seen or seen_add(x) )
            return list(seen_twice)


        def get_files():
            """Gets all files and their info and puts into a nested dict"""

            print("Starting to look for all files in DNAnexus")
            start = time.time()
            files = list(dx.search.find_data_objects(classname='file', describe=True))
            end = time.time()
            total_time = end - start
            print(f"Total time to get all files was {total_time}")

            file_dct = defaultdict(lambda: {"data": []})

            for d in files:
                proj = d['project']
                file_dct[proj]["data"].append({"file_id": d["id"], "name": d["describe"]['name'], "size": d.get('describe',{}).get('size',0), "state": d['describe']['archivalState']})
            
            return file_dct

        def calculate_total():
            """Calculates total cost per project (not taking into account duplicates)"""
            # Cost per GB per month from DNAnexus
            live_storage_cost_month = 0.0257
            # This is an arbitrary number until Wook provides it
            archived_storage_cost_month = 0.0014
            # Get the files dict with the get_files func
            file_info_dict = get_files()
            # Find days in month to work out daily charge
            days_in_month = no_of_days_in_month(self.year, self.month)

            # For each project, add up the sizes of the files 
            # Then convert to GB, multiply by cost per month and divide by days in month to get daily charge estimate
            files_dict = {}
            list_of_files_dicts = []
            for k, v in file_info_dict.items():
                total_size_live = sum([x['size'] for x in v['data'] if x['state'] == "live"])
                total_size_archived = sum([x['size'] for x in v['data'] if x['state'] != "live"])
                total_cost_live = (((total_size_live / (2**30)) * live_storage_cost_month) / days_in_month)
                total_cost_archived = (((total_size_archived / (2**30)) / archived_storage_cost_month) / days_in_month)
                
                files_dict = {"project": k, "total_size_live": total_size_live, "total_size_archived": total_size_archived, 
                            "total_cost_live": total_cost_live, "total_cost_archived": total_cost_archived, 'date':self.today_date}
                
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