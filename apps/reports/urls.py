from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.index, name="index"),
    path("bookings.xlsx", views.bookings_excel, name="bookings_excel"),
    path("revenue.pdf", views.revenue_pdf, name="revenue_pdf"),
]
