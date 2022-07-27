# Ploutos
Ploutos is a Django based web interface to track an organisation's spending on DNAnexus. It gives information on:
- Running Totals: Daily and monthly billing charges calculated according to the running total DNANexus provides.
- Storage Cost: An estimated cost of storage per month (live vs archived) across all projects (default) while allowing you to view this on a more granular level by searching for projects that start or end with a certain string or on a single project level.
- File Type Storage: View the size and counts of files by file type (BAM, FASTQ and VCF) across all projects or similarly on a more granular level. Also displays the total size of files in DNAnexus for the current day in TiB delineated by their state (live vs archived).
- Compute Costs:
- Leaderboard:

## Description
Built with:
- [Django](https://docs.djangoproject.com/en/4.0/ "Django documentation website")
- [MariaDB](https://mariadb.org/, "MariaDB website")
- [Plotly](https://plotly.com/, "Plotly website")
- [Highcharts](https://www.highcharts.com/, "Highcharts website")

## Installation
The required Python package dependencies to query the API, populate the database and view the dashboard can be installed via:
```pip install -r requirements.txt```

Config variables should be passed in a `CREDENTIALS.json` file. This should be placed within Ploutos/Ploutos, the same directory level as `settings.py`.

```json
{
    "DB_USERNAME": "XXX",
    "DB_PASSWORD": "XXX",
    "SECRET_KEY": "XXX",
    "DNANEXUS_TOKEN": "XXX",
    "ORG" : "XXX",
    "LIVE_STORAGE_COST_MONTH" : 123,
    "ARCHIVED_STORAGE_COST_MONTH" : 123,
    "PROJ_COLOUR_DICT": {
        "project_type_1": "rgb(228,26,28)",
        "project_type_2": "rgb(55,126,184)",
        "project_type_3": "rgb(77,175,74)",
        "project_type_4": "rgb(152,78,163)"
    },
    "ASSAY_COLOUR_DICT": {
        "assay_type_1": "rgb(127, 60, 141)",
        "assay_type_2": "rgb(17, 165, 121)",
        "assay_type_3": "rgb(57, 105, 172)",
        "assay_type_4": "rgb(242, 183, 1)"
    }
}
```

To migrate the Django models to the Ploutos database:

```
python manage.py makemigrations
python manage.py migrate
```

## Usage
The script populate_db.py is run daily to grab data from the DNAnexus API and populate the database.
This can be run via the command line:

`python manage.py runscript populate_db`

The server can be run with `python manage.py runserver`.

## Database schema
![Alt text](/Ploutos_db_schema.png "Ploutos db schema")
