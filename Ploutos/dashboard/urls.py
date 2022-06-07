from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('storage/', views.bar_chart, name='storage'),
]
