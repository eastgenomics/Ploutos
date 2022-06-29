import calendar
import datetime as dt
import django_filters as filters

from django import forms
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core.exceptions import ValidationError
from dashboard.models import DailyOrgRunningTotal, StorageCosts

class DateForm(forms.Form):
    """Date and charge type picker for the running totals"""

    # Find earliest object in runningtotals by date + get date
    # This is to set initial date for datepicker + validate
    first_date = str(
        DailyOrgRunningTotal.objects.order_by(
            'date__date'
        ).first().date
    )

    # Get this as date object so datepicker can use as initial
    dateified_earliest_date = dt.datetime.strptime(
        first_date, '%Y-%m-%d'
    ).date()

    # Convert YYY-MM-DD to DD-MM-YYYY for validation message
    # So this fits with what is displayed by the datepicker
    earliest_date = dt.datetime.strptime(
        first_date, "%Y-%m-%d"
    ).strftime("%d/%m/%Y")

    CHARGE_CHOICES = (
        ('All', 'All'),
        ('Storage', 'Storage'),
        ('Compute', 'Compute'),
        ('Egress', 'Egress'),
    )

    start = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'class': 'datepicker',
                'type': 'date',
                'min': f'{first_date}', 'max': dt.date.today()
            }
        )
    )

    end = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'class': 'datepicker',
                'type': 'date',
                'min': f'{first_date}', 'max': dt.date.today()
            }
        )
    )

    charge_type = forms.ChoiceField(
        choices=CHARGE_CHOICES,
        required=True
    )

    def clean(self):
        start = self.cleaned_data['start']
        end = self.cleaned_data['end']
        charge_type = self.cleaned_data['charge_type']

        # Check end date isn't earlier than start date
        # Checking start against earliest db entry and end against today
        # No longer needed as min and max set on date picker itself
        if str(end) < str(start):
            self.add_error("end", "End date is before start date")

        return self.cleaned_data

class MonthlyForm(forms.Form):
    """Year and month choices for the running totals"""

    months_and_years = []
    months_years_present = DailyOrgRunningTotal.objects.annotate(
        month=ExtractMonth('date__date'),
        year=ExtractYear('date__date'),
    ).order_by().values(
            'month','year'
    ).distinct()

    for month_years in months_years_present:
        month=month_years.get('month')
        year=month_years.get('year')
        string=f"{year}-0{month}"
        months_and_years.append(string)

    converted_entries = [
        calendar.month_name[
            int(entry.split("-")[1])
        ]+" "+(entry.split("-")[0])
        for entry in months_and_years
    ]

    # Add option of blank
    converted_entries = ['---'] + converted_entries
    months_and_years = ['---'] + months_and_years

    MONTH_YEAR_CHOICES = (
        (entry, converted_entry)
        for entry, converted_entry in zip(
            months_and_years, converted_entries
            )
        )

    MONTH_YEAR_CHOICES_2 = (
        (entry, converted_entry)
        for entry, converted_entry in zip(
            months_and_years, converted_entries
            )
        )


    start_month = forms.ChoiceField(
        choices=MONTH_YEAR_CHOICES,
        required=False
    )

    end_month = forms.ChoiceField(
        choices=MONTH_YEAR_CHOICES_2,
        required=False
    )

    def clean(self):
        start_month = self.cleaned_data["start_month"]
        end_month = self.cleaned_data["end_month"]

        # Check both start and end entered
        if start_month == "--" and end_month != "--":
            raise ValidationError(
                "If entering a start month please include an end"
            )

        if end_month == "---" and start_month != "---":
            raise ValidationError(
                "If entering an end month please include a start"
        )
        if end_month < start_month:
            self.add_error("end_month", "End month is before start month")

        return self.cleaned_data

class StorageForm(forms.Form):
    """Project type, assay type and monthyear options for the storage costs"""

    TYPE_CHOICES = (
        ('001', '001'),
        ('002', '002'),
        ('003', '003'),
        ('004', '004'),
        )

    ASSAY_CHOICES = (
        ('CEN', 'CEN'),
        ('MYE', 'MYE'),
        ('TWE', 'TWE'),
        ('TSO500', 'TSO500'),
        ('SNP', 'SNP'),
        ('CP', 'CP'),
        ('WES', 'WES'),
        ('FH', 'FH'),
        )

    # Find all the month and years present in db
    months_and_years = []
    months_years_present = StorageCosts.objects.annotate(
        month=ExtractMonth('date__date'),
        year=ExtractYear('date__date'),
    ).order_by().values(
            'month', 'year'
    ).distinct()

    # Append as month-year to a list
    for month_years in months_years_present:
        month = month_years.get('month')
        year = month_years.get('year')
        year_month_string = f"{year}-0{month}"
        months_and_years.append(year_month_string)

    converted_entries = [
        calendar.month_name[
            int(entry.split("-")[1])
        ]+" "+(entry.split("-")[0])
        for entry in months_and_years
    ]
    # Add in option of blank as choice
    converted_entries = ['---'] + converted_entries
    months_and_years = ['---'] + months_and_years
    # Set as tuple choices
    MONTH_YEAR_CHOICES = (
        (entry, converted_entry)
        for entry, converted_entry in zip(
            months_and_years, converted_entries
        )
    )
    MONTH_YEAR_CHOICES_2 = (
        (entry, converted_entry)
        for entry, converted_entry in zip(
            months_and_years, converted_entries
        )
    )

    project_type = forms.CharField(
        required=False,
        label='Project type',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter project types, separated by commas',
                'style': 'width:340px',
                'class': 'form-control'
            }
        )
    )

    assay_type = forms.CharField(
        required=False,
        label='Assay type',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter assay types, separated by commas',
                'style': 'width:340px',
                'class': 'form-control'
            }
        )
    )

    start = forms.ChoiceField(
        label='Earliest month',
        choices=MONTH_YEAR_CHOICES,
        required=True,
    )

    end = forms.ChoiceField(
        label='Latest month',
        choices=MONTH_YEAR_CHOICES_2,
        required=True,
    )

    def clean(self):
        project_type = self.cleaned_data["project_type"]
        assay_type = self.cleaned_data["assay_type"]
        start = self.cleaned_data["start"]
        end = self.cleaned_data["end"]

        # Check whether >1 entries are in both proj and assay type by comma
        if project_type and assay_type:
            if (project_type.find(",") != -1) or (assay_type.find(",") != -1):
                raise ValidationError(
                    "If using both project type and assay type filters, "
                        "please only enter one of each"
                )

        # Check both start and end included
        if start == "---" and end != "---":
            raise ValidationError(
                "If entering an end please include a start"
            )

        if end == "---" and start != "---":
            raise ValidationError(
                "If entering a start please include an end"
        )

        # Check end month not before start
        if end < start:
            raise ValidationError(
                "Please ensure start month is before end month"
            )

        return self.cleaned_data
