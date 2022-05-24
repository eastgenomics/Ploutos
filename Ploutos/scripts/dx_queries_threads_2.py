

"""
    Script to return files for project in org.
    ------------------------------------------

    This script runs in 84.7512870311737 minutes in testing (using 10 threads).
    X minutes with 100 threads.
    It uses multithreading to spin out requests by projects.
    It returns a list of all files with only certain fields.
    Parameters
    ----------


    Returns:
        list: all files in org by project.

"""

import concurrent.futures
import dxpy as dx
import json
import os
from pathlib import Path
import time


def get_data_objs(project):
    """
    Args:
        project - project to find.
        L - shared list variable
    Return all data objects for specified project.
    writes list of dicts to json file.
    This takes 25 minutes to run.
    """
    data = dx.bindings.search.find_data_objects(project=str(project),
                                                classname='file',
                                                # describe=True,
                                                describe={'fields': {'name': True, 'created': True, 'archivalState': True, 'size': True}})

    print(f"done -- {project}")

    return data


def get_all_projects():
    """
    Return list of all projects from DNAnexus
    Returns:
        list: List of project ids
    """

    project_list_all = []

    projects = dx.search.find_projects(name="*",
                                       name_mode="glob",
                                       billed_to='org-emee_1',
                                       describe=True
                                       )

    for project in projects:
        project_list_all.append(project['id'])
    print("Total projects found:", len(project_list_all))

    return project_list_all


def DNAnexus_login():  # --> None
    """
    Extracts Token and uses to login to DNAnexus and access API.
    """
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    # Could add this to env vars?
    BASE_DIR = Path(__file__).resolve().parent.parent

    with open(os.path.join(os.path.dirname(BASE_DIR),
                           'Ploutos/CREDENTIALS.json')) as c:
        CREDENTIALS = json.load(c)

    AUTH_TOKEN = CREDENTIALS['DNA_NEXUS_SECRET_KEY']

    # env variable for dx authentication
    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": AUTH_TOKEN
    }
    # set token to env
    dx.set_security_context(DX_SECURITY_CONTEXT)


def main():
    # Set-up
    start = time.time()
    print(time.ctime())
    DNAnexus_login()
    List = []
    Projects = list(get_all_projects())

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its proj
        for i in executor.map(get_data_objs, Projects):
            try:
                data = i.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (proj, exc))
            else:
                #print('%r page is %d bytes' % (proj, len(data)))
                List.append(list(data))

        # future_to_proj = {executor.submit(
        #     get_data_objs, proj): proj for proj in Projects}
        # for future in concurrent.futures.as_completed(future_to_proj):
        #     proj = future_to_proj[future]
        #     try:
        #         data = future.result()
        #     except Exception as exc:
        #         print('%r generated an exception: %s' % (proj, exc))
        #     else:
        #         #print('%r page is %d bytes' % (proj, len(data)))
        #         List.append(list(data))
    json_object2 = list(List)
    print(len(json_object2))
    with open("all_data_objects_threads_100.json", "w") as file:
        json.dump(json_object2, file)
    time_taken = (time.time() - start)/60
    print(time_taken)



if __name__ == "__main__":
    main()
