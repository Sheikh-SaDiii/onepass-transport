from django.contrib import admin
from .models import Route, Transport, Schedule


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("origin", "destination", "distance_km")
    search_fields = ("origin", "destination")


@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "provider", "total_seats", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("code", "name", "registration_no")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("transport", "route", "departure", "arrival", "fare", "status")
    list_filter = ("status", "transport__kind")
    date_hierarchy = "departure"
