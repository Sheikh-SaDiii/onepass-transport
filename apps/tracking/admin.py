from django.contrib import admin
from .models import GPSPing


@admin.register(GPSPing)
class GPSPingAdmin(admin.ModelAdmin):
    list_display = ("transport", "lat", "lng", "speed_kmh", "status", "recorded_at")
    list_filter = ("status",)
