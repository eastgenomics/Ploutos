"""
This script contains functions for querying DNAnexus API for files, projects
and other data to be stored in MariaDB for the DNAnexus monitoring app.

Changes to make:
 - Add standard naming use get instead of find.
 -

"""

import json
import time
import dxpy as dx


def get_002_projects():
    """
    Return list of 002 sequencing projects from DNAnexus
    Returns:
        list: List of project ids
    """

    project_list_002 = []

    projects = dx.search.find_projects(name="002_*",
                                       name_mode="glob")

    for project in projects:
        project_list_002.append(dx.DXProject(project["id"]))

    # project_002_list = [x["id"] for x in projects] # Alternative list comp

    print("Total 002 projects found:", len(project_list_002))

    return project_list_002


def get_all_projects(org):
    """
    Return list of all projects from DNAnexus
    Returns:
        list: List of project ids
    """

    project_list_all = []

    projects = dx.search.find_projects(name="*",
                                       name_mode="glob"
                                       # billTo=str(org) - not working?
                                       )

    for project in projects:
        project_list_all.append(dx.DXProject(project["id"]))
    # project_all_list = [x["id"] for x in projects] # Alternative list comp
    print("Total projects found:", len(project_list_all))

    return project_list_all


def get_all_data_objs():
    """
    Args:
        org (string)
    Return all data objects.
    writes list of dicts to json file.
    This takes X minutes to run.

    """
    data_objs = dx.bindings.search.find_data_objects(describe=False,
                                                     # limit=1000,
                                                     # for use in testing only
                                                     classname='file')
    data_objs_list = []
    for obj in data_objs:
        data_objs_list.append(obj)
        # data_objs_list.append(obj)

    json_object1 = json.dumps(data_objs_list, indent=4)
    with open("all_data_objs.json", "a") as outfile:
        outfile.write(json_object1)

    print("Total project data objects found:", len(data_objs_list))
    #print(data_objs_list)

    return data_objs_list

def get_dups(files):
    """
    Solution:
    This takes all the file ids and sorts them depending on if they are unique
    or a duplicate. This could be incorporated into another function to allow
    for sorting while processing files by project to calculate storage costs.

    Returns:
        dup_data_objs: list of duplicate data objects (i.e. seen twice or seen2)
    Credit: JohnLaRooy - StackOverflow

    Development:
    - Currently not working with large lists as comes up with unhashable.

    """
    values = []
    projects = []
    for item in files:
        values.append(item['id'])
        projects.append(item['project'])
    values = tuple(values)
    projects = tuple(projects)
    seen = set()
    seen_project = {}
    seen2 = set()
    seen2_project = {}
    seen_add = seen.add
    seen2_add = seen2.add
    for i, pro in zip(values, projects):
        if i in seen:
            if i not in seen2:
                seen2_add(i)
                seen2_project.update({i: [seen_project.get(i), pro]})
            else:
                print(seen_project.get(i))
                print(seen2_project.get(i))
                seen2_project.update(
                    {i: [seen2_project.get(i), pro]})
        else:
            seen_add(i)
            seen_project.update({i: pro})
    dup_data_objs = list(seen2)
    dup_data_objs_projects = seen2_project

    return dup_data_objs, dup_data_objs_projects


# def get_dups2(files):
#     """
#     Solution:
#     This takes all the file ids and sorts them depending on if they are unique
#     or a duplicate. This could be incorporated into another function to allow
#     for sorting while processing files by project to calculate storage costs.

#     Returns:
#         dup_data_objs: list of duplicate data objects (i.e. seen twice or seen2)
#     Credit: JohnLaRooy - StackOverflow
#     """
#     values = []
#     for item in files:
#         values.append(item['id'])
#     values = tuple(values)
#     seen = set()
#     seen2 = set()
#     seen_add = seen.add
#     seen2_add = seen2.add
#     for item in values:
#         if item in seen:
#             seen2_add(item)
#         else:
#             seen_add(item)
#     return list(seen2)


# def get_dups():
#     """
#     Function: get_dups()
#     What it does? This finds all the files in DNAnexus for org given.
#     And then finds all files which are present in multiple projects,
#     and therefore require special treatment to calculate costs.
#     Args: ORG- The id for your organisation
#     Returns: list of file ids?
#     """
#     print("get_dups Starting")



def main():
    with open('Ploutos/CREDENTIALS.json') as c:
        CREDENTIALS = json.load(c)

    AUTH_TOKEN = CREDENTIALS['DNA_NEXUS_SECRET_KEY']

    # env variable for dx authentication
    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": AUTH_TOKEN
    }
    # set token to env
    dx.set_security_context(DX_SECURITY_CONTEXT)

    # main function
    print("main function starting")
    start_time = time.time()
    # Print the current date and time in readable format
    print('\nToday is: ', time.ctime(start_time))
    projects = get_all_projects('org-emee_1')
    print(len(projects))
    all_objects = get_all_data_objs()
    print(len(all_objects))
    #list_files = get_dups(all_objects)
    list_files, list_pros = get_dups(all_objects)
    print(len(list_files))
    # print(list_files)
    print(len(list_pros))
    print(list_pros)
    print('\nEnd Time is: ', time.ctime(time.time()))
    print(f"--- {(time.time() - start_time)} seconds ---")


if __name__ == '__main__':
    main()
