from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('storage/', views.storage_chart, name='storage'),
    path('jobs/', views.jobs, name='jobs')
]
