from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("seats/<int:schedule_id>/", views.select_seats, name="select_seats"),
    path("create/<int:schedule_id>/", views.create_booking, name="create"),
    path("checkout/<str:pnr>/", views.checkout, name="checkout"),
    path("pay/<str:pnr>/", views.pay, name="pay"),
    path("ticket/<str:pnr>/", views.ticket, name="ticket"),
    path("mine/", views.my_bookings, name="my_bookings"),
    path("cancel/<str:pnr>/", views.cancel_booking, name="cancel"),
    path("invoice/<str:pnr>/", views.invoice, name="invoice"),
]
