import datetime as dt
import json
import pandas as pd
import sys

from collections import defaultdict
from dashboard.models import Users, Projects, Dates, DailyOrgRunningTotal, StorageCosts
from django.apps import apps
from django.conf import settings
from time import time, localtime, strftime

def run():
    do_stuff()

def do_stuff():
    today_date = dt.datetime.now().strftime("%Y/%m/%d").replace("/", "-")

    # Opening JSON file
    with open("/home/rebecca/Ploutos/Ploutos/project_storage_totals.json") as f:
        storage_data = json.load(f)

    for key, value in storage_data.items():
        new_storage, created = StorageCosts.objects.get_or_create(
            project = Projects.objects.get(dx_id=key),
            unique_size_live = value['unique_live']['size'],
            unique_cost_live = value['unique_live']['cost'],
            unique_size_archived = value['unique_archived']['size'],
            unique_cost_archived = value['unique_archived']['cost'],

            total_size_live = value['total_live']['size'],
            total_cost_live = value['total_live']['cost'],
            total_size_archived = value['total_archived']['size'],
            total_cost_archived = value['total_archived']['cost'],
            date = Dates.objects.get(date=today_date),
            )

