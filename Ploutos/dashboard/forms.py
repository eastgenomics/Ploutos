from django import forms
import datetime
from django.core.exceptions import ValidationError

class DateForm(forms.Form):

    start = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    end = forms.DateField(widget=forms.DateInput(attrs={'class':'datepicker', 'type':'date'}))

    def clean_end(self):
        """docstring"""
        data = self.cleaned_data['end']
        if data > str(datetime.date.today()):
           raise forms.ValidationError("End date is in the future!")
        return self.cleaned_data


