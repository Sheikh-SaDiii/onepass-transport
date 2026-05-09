from django.urls import path
from . import views

app_name = "qr"

urlpatterns = [
    path("scan/", views.scanner, name="scanner"),
    path("verify/", views.verify, name="verify"),
]
