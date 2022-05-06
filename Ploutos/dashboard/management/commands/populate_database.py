from django.core.management.base import BaseCommand, CommandError
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal
from django.apps import apps
import pandas as pd
import os.path as path


class Command(BaseCommand):
    help = "Loads projects and project storage from CSV file and imports them into the database."

    def handle(self, *args, **options):
        
        BASE_DIR =  path.abspath(path.join(__file__ ,"../../../.."))
        with open(path.join(path.dirname(BASE_DIR), 'projects.csv')) as f:
            projects_df = pd.read_csv(f, sep='\t')

        with open(path.join(path.dirname(BASE_DIR), 'running_totals.csv')) as totals:
            running_tots_df = pd.read_csv(totals, sep='\t')

        for index, row in projects_df.iterrows():
            #Add users to users table
            user, created = Users.objects.get_or_create(
                user_name = row['created_by'],
            )

            a_new_date, created = Dates.objects.get_or_create(
                date = row['created'],
            )
            
            # Get all the project objects
            projects_data = Projects.objects.all()

            # Get names of projects from csv
            new_name = row['name']

            # Dict to filter projects using dx_id from csv
            filter_dict = {
                "dx_id": row['dx_id'],
            }

            # Filter projects in db by dx_id from csv
            found_row = projects_data.filter(**filter_dict)

            # If already in database, get the name
            if found_row:
                existing_project = found_row.values_list(
                    "name", flat=True
                ).get()

                # If the existing proj name is not same as name in csv update it
                if existing_project != new_name:
                    found_row.update(name=new_name)

            # Get or create project objects
            project, created = Projects.objects.get_or_create(
                dx_id = row['dx_id'],
                name = row['name'],
                created_by = user,
                created = a_new_date,
            )

            # For second totals csv 
        for index, row in running_tots_df.iterrows():
            # Add to dates table and create ids for each date
            new_date, created = Dates.objects.get_or_create(
                date = row['date'],
            )

            # Add running totals to totals table
            total, created = DailyOrgRunningTotal.objects.get_or_create(
                date = new_date,
                storage_charges = row['storage_charges'],
                compute_charges = row['compute_charges'],
                egress_charges = row['egress_charges'],
                estimated_balance = row['estimated_balance'],
            )