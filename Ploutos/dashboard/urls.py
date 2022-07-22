from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('storage/', views.storage_chart, name='storage'),
    path('compute/', views.compute_graph, name='compute'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
