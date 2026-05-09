from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path("live/<int:transport_id>/", views.live, name="live"),
    path("push/<int:transport_id>/", views.push_ping, name="push"),
    path("latest/<int:transport_id>/", views.latest, name="latest"),
]
