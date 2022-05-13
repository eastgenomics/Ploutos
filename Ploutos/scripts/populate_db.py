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

        # Adding dates to table
        a_new_date, created = Dates.objects.get_or_create(
            date=datetime.datetime.fromtimestamp(project_dict['created']/1000).strftime('%Y-%m-%d'),)

        # Adding project details to table
        project, created = Projects.objects.update_or_create(
                dx_id = project_dict['id'],
                name = project_dict['name'],
                created_by = user,
                created = a_new_date,
            )
