import datetime as dt

from django import forms
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
        initial=dateified_earliest_date,
        widget=forms.DateInput(
            attrs={
                'class': 'datepicker',
                'type': 'date'
            }
        )
    )

    end = forms.DateField(
        initial=dt.date.today(),
        widget=forms.DateInput(
            attrs={
                'class': 'datepicker',
                'type': 'date'
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

        # Check start date isn't before earliest db entry
        # Assign error to the specific field
        if str(start) < self.first_date:
            self.add_error("start",
                "Start date earlier than the earliest entry in the database."
                    f" Current earliest date is {self.earliest_date}"
            )

        # Check end date isn't after today
        # Assign error to the specific field
        if str(end) > str(dt.date.today()):
            self.add_error("end", "The end date is in the future")

        return self.cleaned_data


class StorageForm(forms.Form):
    """Project type, assay type and monthyear picker for the storage costs"""

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

    # Find years from db
    years = list(StorageCosts.objects.order_by().values_list(
        'date__date__year', flat=True
        ).distinct())

    # Find months from db
    months = list(StorageCosts.objects.order_by().values_list(
        'date__date__month', flat=True
        ).distinct())

    YEAR_CHOICES = ((year, year) for year in years)

    MONTH_CHOICES = (
        ('All', 'All'),
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    )

    project_type = forms.CharField(
        required=False,
        label='Project type',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter project types, separated by commas',
                'style': 'width:320px'
            }
        )
    )

    assay_type = forms.CharField(
        required=False,
        label='Assay type',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter assay types, separated by commas',
                'style': 'width:320px'
            }
        )
    )
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=True
    )

    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True
    )

    def clean(self):
        project_type = self.cleaned_data["project_type"]
        assay_type = self.cleaned_data["assay_type"]
        year = self.cleaned_data["year"]
        month = self.cleaned_data["month"]

        # Only May and June are in the db currently
        stringified_months = [
            str(x) for x in self.months
        ]

        acceptable_months = stringified_months + ['All']

        # Check whether >1 entries are in both proj and assay type by comma
        if project_type and assay_type:
            if (project_type.find(",") != -1) or (assay_type.find(",") != -1):
                raise ValidationError(
                    "If using both project type and assay type filters, "
                        "please only enter one of each"
                )

        # Check whether user is choosing months with no data currently
        if month not in acceptable_months:
            raise ValidationError(
                "There are no database entries for the specified month"
            )

        return self.cleaned_data
