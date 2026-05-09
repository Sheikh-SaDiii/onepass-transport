from django.contrib import admin
from .models import Booking, BookedSeat


class SeatInline(admin.TabularInline):
    model = BookedSeat
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("pnr", "user", "schedule", "total_amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("pnr", "user__username", "user__email")
    inlines = [SeatInline]
