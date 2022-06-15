# Ploutos
Webapp for tracking DNAnexus billing project.

## Configuration
Config variables should be passed in a CREDENTIALS.json file.

This should be placed within Ploutos/Ploutos, within the same directory level as settings.py.

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
## Usage notes
The script populate_db.py is run daily to grab data from the DNAnexus API and populate the database.
This can be run via the command line:

`python manage.py runscript populate_db`

