from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, ProviderProfile, DriverProfile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_approved", "wallet_balance", "is_staff")
    list_filter = ("role", "is_approved", "is_staff", "is_superuser")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("OnePass", {"fields": ("role", "phone", "avatar", "wallet_balance", "is_approved")}),
    )


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ("company_name", "provider_code", "transport_kind", "user", "created_at")
    list_filter = ("transport_kind",)
    search_fields = ("company_name", "provider_code")


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("driver_code", "user", "provider", "license_no", "created_at")
    search_fields = ("driver_code", "license_no")
