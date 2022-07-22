from datetime import date
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
        return str(self.date)

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
    date = models.OneToOneField(Dates, on_delete=models.CASCADE)
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


class FileTypes(models.Model):
    """Model representing a file type"""
    file_type = models.CharField(max_length=35, unique=True)


class FileTypeState(models.Model):
    """Model representing the size and count of file types"""
    file_type = models.ForeignKey(FileTypes, on_delete=models.CASCADE)
    file_count_live = models.IntegerField()
    file_count_archived = models.IntegerField()
    file_size_live = models.FloatField()
    file_size_archived = models.FloatField()


class FileTypeDate(models.Model):
    """
    Model representing the state of files for a project on a given date
    """
    date = models.ForeignKey(Dates, on_delete=models.CASCADE)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    file_state = models.ForeignKey(FileTypeState, on_delete=models.CASCADE)


class Executables(models.Model):
    executable_name = models.CharField(max_length=200)
    version = models.CharField(max_length=10)

    def __str__(self):
        return self.excutable_name


class ComputeCosts(models.Model):
    dx_id = models.CharField(max_length=200)
    # job_name = models.CharField(max_length=200)
    executable_name = models.ForeignKey(Executables, on_delete=models.CASCADE)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    runtime = models.DurationField()
    total_cost = models.FloatField()
    state = models.CharField(max_length=50)
    launched_by = models.ForeignKey(Users, on_delete=models.CASCADE)
    date = models.ForeignKey(Dates, on_delete=models.CASCADE)

    def __str__(self):
        return self.dx_id
