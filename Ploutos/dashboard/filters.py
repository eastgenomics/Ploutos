import django_filters

from dashboard.models import *

class StorageCostsFilter(django_filters.FilterSet):
    class Meta:
        model = StorageCosts
        fields = '__all__'