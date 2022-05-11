"""
    Script to add data to MariaDB.
"""

from dashboard.models import Users, Dates, Projects
import queries as q
import datetime


def run():
    """Main function
    """
    q.DNAnexus_login()
    populate_projects()


def populate_projects():
    """
    Populate database with data from API query.
    Example data in project.describe():

    {'id': 'project-G1KpVq04BJ5ZG7BY36XPx18j',
    'name': '002_170814_170816_NS500192_171109_K00178',
    'class': 'project', 'created': 1616750828000, 'modified': 1649246463638,
    'billTo': 'org-emee_1', 'cloudAccount': 'cloudaccount-dnanexus',
    'level': 'CONTRIBUTE', 'dataUsage': 18.170017506927252,
    'sponsoredDataUsage': 0, 'remoteDataUsage': 0, 'region': 'aws:eu-central-1',
    'summary': '', 'description': '', 'protected': True, 'restricted': False,
    'downloadRestricted': False,
    'currency': {'dxCode': 0, 'code': 'USD', 'symbol': '$',
                'symbolPosition': 'left', 'decimalSymbol': '.',
                'groupingSymbol': ','},
    'containsPHI': False, 'createdBy': {'user': 'user-toutoua'},
    'version': 1, 'archivedDataUsage': 12.773729707114398,
    'storageCost': 0.20255324499076233, 'pendingTransfer': None,
    'tags': [], 'defaultInstanceType': 'mem1_ssd1_x4',
    'totalSponsoredEgressBytes': 0, 'consumedSponsoredEgressBytes': 0,
    'provider': {}, 'atSpendingLimit': False}

    """

    # all_data_objs = q.find_all_data_objs()
    all_projects = q.get_all_projects('org-emee_1')
    for project in all_projects:
        project_dict = project.describe()
        print(project_dict)
        # Adding Users to table
        user, created = Users.objects.get_or_create(
            user_name=project_dict['createdBy']['user'],)

        # Adding dates
        a_new_date, created = Dates.objects.get_or_create(
            date=datetime.datetime.fromtimestamp(project_dict['created']/1000).strftime('%Y-%m-%d'),)

# for index, row in projects_df.iterrows():
#             #Add users to users table
#             user, created = Users.objects.get_or_create(
#                 user_name = row['created_by'],
#             )

#             # Add project created dates to Dates table to make IDs
#             a_new_date, created = Dates.objects.get_or_create(
#                 date = row['created'],
#             )

#             # Filtering for updating existing project names in table in case they have been changed in DNAnexus
#             # Get all the project objects
#             projects_data = Projects.objects.all()

#             # Get names of projects from csv
#             new_name = row['name']

#             # Dict to filter projects using dx_id from csv
#             filter_dict = {
#                 "dx_id": row['dx_id'],
#             }

#             # Filter projects in db by dx_id from csv
#             found_row = projects_data.filter(**filter_dict)

#             # If already in database, get the name
#             if found_row:
#                 existing_project = found_row.values_list(
#                     "name", flat=True
#                 ).get()

#                 # If the existing proj name is not same as name in csv update it
#                 if existing_project != new_name:
#                     found_row.update(name=new_name)

#             # Get or create project objects
#             project, created = Projects.objects.get_or_create(
#                 dx_id = row['dx_id'],
#                 name = row['name'],
#                 created_by = user,
#                 created = a_new_date,
#             )
