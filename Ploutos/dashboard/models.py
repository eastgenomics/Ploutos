from django.db import models

# Create your models here.
class storage_costs(models.Model):
    name = models.CharField(max_length=100, blank = True, null = True)
    project_id = models.IntegerField(blank = True, null = True)
    # date = models.DateField(blank = True, null = True)
    storage_data = models.FloatField(blank = True, null = True)
    archival_state = models.IntegerField(blank = True, null = True)

    def __str__(self):
        return self.name


class projects(models.Model):
    dx_id = models.CharField(max_length=100, blank = False, null = False)
    name = models.CharField(max_length=200, blank = False, null = False)
    created = models.IntegerField(blank = False, null = False)
    created_by = models.IntegerField(blank = False, null = False)

    def __str__(self):
        return self.name


class daily_org_running_total(models.Model):
    storage_charges = models.FloatField(blank = False, null = False)
    compute_charges = models.FloatField(blank = False, null = False)
    egress_charges = models.FloatField(blank = False, null = False)
    storage_charges = models.FloatField(blank = False, null = False)
    date_id = models.IntegerField(blank = False, null = False)

    def __str__(self):
        return self.name


class dates(models.Model):
    date = models.IntegerField(blank = False, null = False)

    def __str__(self):
        return self.name


class users(models.Model):
    user_name = models.CharField(max_length=100, blank = False, null = False)

    def __str__(self):
        return self.name


class compute_costs(models.Model):
    executable_id = models.IntegerField()
    project_id = models.IntegerField()
    # intstance_id = models.IntegerField(blank = True, null = True)
    runtime = models.IntegerField()
    total_cost = models.FloatField()
    launched_by = models.IntegerField()
    date_id = models.IntegerField()

    def __str__(self):
        return self.name


class executables(models.Model):
    executable_id = models.IntegerField()
    dx_id = models.CharField(max_length=200, blank = False, null = False)
    excutable_name = models.CharField(max_length=200, blank = False, null = False)
    version = models.CharField(max_length=30, blank = False, null = False)

    def __str__(self):
        return self.name


# class AllFields(models.Model):
#     name = models.CharField(max_length=50, blank = True, null = True)
#     slug = models.SlugField(default = 'test')
#     date = models.DateField(blank = True, null = True)
#     float = models.FloatField(blank = True, null = True)
#     json = models.JSONField()
#     id_for_something = models.PositiveIntegerField() # Zero - 9223372036854775807 accepted
#     unique_id = models.UUIDField() #Used for postgres and other uses.
#     # More here: https://docs.djangoproject.com/en/4.0/ref/models/fields/
#     def __str__(self):
#         return self.name
