from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("wallet/", views.wallet, name="wallet"),
    path("topup/", views.topup, name="topup"),
]
