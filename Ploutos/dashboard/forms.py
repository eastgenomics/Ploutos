from django import forms
import datetime
from django.core.exceptions import ValidationError

class DateForm(forms.Form):
    """Date and charge type picker for the running totals"""
    CHARGE_CHOICES = (
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
        cleaned_data = super(DateForm, self).clean()
        start = cleaned_data['start']
        end = cleaned_data['end']
        charge_type = cleaned_data['charge_type']
        #error_messages = []

        if str(start) < "2022-05-06":
            self.add_error("start", "Start date is earlier than the earliest entry in the database")

        if str(end) > str(datetime.date.today()):
            self.add_error("end", "End date is in the future")

        return cleaned_data


class StorageForm(forms.Form):

    TYPE_CHOICES= (
        ('001','001'),
        ('002','002'),
        ('003','003'),
        ('004','004'),
        )
    ASSAY_CHOICES= (
        ('1','CEN'),
        ('2','MYE'),
        ('3','TWE'),
        ('4','TSO500'),
        ('5','SNP'),
        ('6','CP'),
        ('7','WES'),
        ('8','FH'),
        )
    project_type = forms.MultipleChoiceField(choices=TYPE_CHOICES, widget=forms.CheckboxSelectMultiple())
    assay_type = forms.MultipleChoiceField(choices=ASSAY_CHOICES, widget=forms.CheckboxSelectMultiple(), required=False)
    
    # def clean(self):
    #     project_type = self.cleaned_data["project_type"]
    #     assay_type = self.cleaned_data["assay_type"]

    #     # if project_type and assay_type:
    #     #     raise ValidationError("Please fill in either project type or assay type, not both")
    #     return self.cleaned_data

