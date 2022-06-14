# Ploutos
Webapp for tracking DNAnexus billing project.

## Configuration
Credentials should be passed in a CREDENTIALS.json file.

This should be placed within Ploutos/Ploutos, within the same directory level as settings.py.

```json
{
    "DB_USERNAME": "XXX",
    "DB_PASSWORD": "XXX",
    "SECRET_KEY": "XXX",
    "DNANEXUS_TOKEN": "XXX",
    "ORG" : "XXX",
    "LIVE_STORAGE_COST_MONTH" : 123,
    "ARCHIVED_STORAGE_COST_MONTH" : 123
}
```
## Usage notes
The script populate_db.py is run daily to grab data from the DNAnexus API and populate the database.
This can be run via the command line:

`python manage.py runscript populate_db`

