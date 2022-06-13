from django import forms
import datetime
from django.core.exceptions import ValidationError
from dashboard.models import StorageCosts

class DateForm(forms.Form):
    """Date and charge type picker for the running totals"""
    CHARGE_CHOICES = (
        ('All','All'),
        ('Storage', 'Storage'),
        ('Compute', 'Compute'),
        ('Egress','Egress'),
    )

    start = forms.DateField(widget=forms.DateInput(attrs={
        'class':'datepicker', 'type':'date'
        }))
    end = forms.DateField(widget=forms.DateInput(attrs={
        'class':'datepicker', 'type':'date'
        }))
    charge_type = forms.ChoiceField(choices = CHARGE_CHOICES, required=True)

    def clean(self):
        start = self.cleaned_data['start']
        end = self.cleaned_data['end']
        charge_type = self.cleaned_data['charge_type']

        if str(start) < "2022-05-06":
            self.add_error("start", "Start date is earlier than the earliest entry in the database")

        if str(end) > str(datetime.date.today()):
            self.add_error("end", "End date is in the future")

        return self.cleaned_data

class StorageForm(forms.Form):
    """Project type and assay type picker for the storage costs"""

    TYPE_CHOICES= (
        ('001','001'),
        ('002','002'),
        ('003','003'),
        ('004','004'),
        )
    ASSAY_CHOICES= (
        ('CEN','CEN'),
        ('MYE','MYE'),
        ('TWE','TWE'),
        ('TSO500','TSO500'),
        ('SNP','SNP'),
        ('CP','CP'),
        ('WES','WES'),
        ('FH','FH'),
        )
    
    years = list(StorageCosts.objects.order_by().values_list('date__date__year',flat=True).distinct())
    YEAR_CHOICES = ((year, year) for year in years)

    MONTH_CHOICES = (
        ('All','All'),
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

    #project_type = forms.MultipleChoiceField(choices=TYPE_CHOICES, widget=forms.CheckboxSelectMultiple(), required=False)
    project_type = forms.CharField(required=False, label='Project type', 
                    widget=forms.TextInput(attrs={'placeholder': 'Enter project types, separated by commas', 'style': 'width:300px'}))
    assay_type = forms.CharField(required=False, label='Assay type', 
                    widget=forms.TextInput(attrs={'placeholder': 'Enter assay types, separated by commas', 'style': 'width:300px'}))
    #assay_type = forms.MultipleChoiceField(choices=ASSAY_CHOICES, widget=forms.CheckboxSelectMultiple(), required=False)
    year = forms.ChoiceField(choices = YEAR_CHOICES, required=True)
    month = forms.ChoiceField(choices = MONTH_CHOICES, required=True)
    #month = forms.ChoiceField(choices = MONTH_CHOICES, required=False)
    
    def clean(self):
        project_type = self.cleaned_data["project_type"]
        assay_type = self.cleaned_data["assay_type"]
        year = self.cleaned_data["year"]

        if project_type and assay_type:
            if project_type.find(",") !=-1 or assay_type.find(",") != -1:
                raise ValidationError("If using both project type and assay type filters, please only enter one of each")
        return self.cleaned_data

