from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    PROVIDER = "provider", "Service Provider"
    USER = "user", "User"


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_approved = models.BooleanField(default=True)
    firebase_uid = models.CharField(max_length=128, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN or self.is_superuser

    @property
    def is_provider(self):
        return self.role == Role.PROVIDER

    @property
    def is_user(self):
        return self.role == Role.USER

    @property
    def is_pending_approval(self):
        return self.is_provider and not self.is_approved


class TransportKind(models.TextChoices):
    BUS = "bus", "Bus"
    TRAIN = "train", "Train"
    PLANE = "plane", "Plane"
    SHIP = "ship", "Ship/Launch"
    METRO = "metro", "Metro Rail"


class ProviderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider_profile")
    company_name = models.CharField(max_length=200)
    transport_kind = models.CharField(max_length=10, choices=TransportKind.choices)
    provider_code = models.CharField(max_length=64, unique=True, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to="provider_logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.provider_code:
            slug = "".join(c for c in self.company_name.lower() if c.isalnum()) or "company"
            count = ProviderProfile.objects.filter(transport_kind=self.transport_kind).count() + 1
            self.provider_code = f"{self.transport_kind}_{slug}{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name} [{self.provider_code}]"


class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name="drivers"
    )
    driver_code = models.CharField(max_length=64, unique=True, blank=True)
    license_no = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.driver_code:
            count = DriverProfile.objects.filter(provider=self.provider).count() + 1
            self.driver_code = f"{self.provider.provider_code}_driver{count:02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} [{self.driver_code}]"
