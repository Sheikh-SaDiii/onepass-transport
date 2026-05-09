from django.urls import path
from . import views

app_name = "transports"

urlpatterns = [
    path("search/", views.search, name="search"),
    path("manage/", views.manage_transports, name="manage"),
    path("add/", views.add_transport, name="add"),
    path("<int:pk>/delete/", views.delete_transport, name="delete"),
    path("schedule/add/", views.add_schedule, name="add_schedule"),
    path("schedule/delete-all/", views.delete_all_schedules, name="delete_all_schedules"),
    path("schedule/series/<str:series_id>/delete/", views.delete_series, name="delete_series"),
    path("schedule/<int:pk>/delete/", views.delete_schedule, name="delete_schedule"),
]
