from django.db import models

# Create your models here.
class Users(models.Model):
    """Model representing an org user"""
    user_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.user_name

class Dates(models.Model):
    """Model representing a date.
    N.B. date has to be in YYYY-MM-DD format """
    date = models.DateField(unique=True)

    def __str__(self):
        return self.date

class Projects(models.Model):
    """Model representing a project."""
    dx_id = models.CharField(max_length=35, unique=True)
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE)
    created = models.ForeignKey(Dates, on_delete=models.CASCADE)

    def __str__(self):
        return self.dx_id

class DailyOrgRunningTotal(models.Model):
    """Model representing running totals for the org"""
    date = models.ForeignKey(Dates, on_delete=models.CASCADE, unique=True)
    storage_charges = models.FloatField()
    compute_charges = models.FloatField()
    egress_charges = models.FloatField()
    estimated_balance = models.FloatField()



class StorageCosts(models.Model):
    """Model representing storage costs per project"""
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    unique_size_live = models.FloatField()
    unique_size_archived = models.FloatField()
    total_size_live = models.FloatField()
    total_size_archived = models.FloatField()
    unique_cost_live = models.FloatField()
    unique_cost_archived = models.FloatField()
    total_cost_live = models.FloatField()
    total_cost_archived = models.FloatField()
    date = models.ForeignKey(Dates, on_delete=models.CASCADE)

#    def __str__(self):
#        return self.name

class Executables(models.Model):
    executable_id = models.AutoField(primary_key=True)
    dx_id = models.CharField(max_length=200)
    excutable_name = models.CharField(max_length=200)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    #version = models.CharField(max_length=30)

#    def __str__(self):
#        return self.name


class ComputeCosts(models.Model):
    executable_id = models.ForeignKey(Executables, on_delete=models.CASCADE)
    # intstance_id = models.IntegerField(blank = True, null = True)
    # runtime = models.IntegerField()
    total_cost = models.FloatField()
    launched_by = models.ForeignKey(Users, on_delete=models.CASCADE)
    date = models.ForeignKey(Dates, on_delete=models.CASCADE)
    # project = models.ForeignKey(Projects, on_delete=models.CASCADE)

#    def __str__(self):
#        return self.name


# Models in progress

# class Egress(models.Model):
#     project = models.ForeignKey(Projects,on_delete=models.CASCADE)
#     egress_cost = models.FloatField()
#     date = models.ForeignKey(Dates, on_delete=models.CASCADE)

#     def __str__(self):
#         return self.project
