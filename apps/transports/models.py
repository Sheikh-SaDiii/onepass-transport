from django.db import models
from apps.accounts.models import ProviderProfile, DriverProfile, TransportKind


class Route(models.Model):
    origin = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    distance_km = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("origin", "destination")
        ordering = ["origin", "destination"]

    def __str__(self):
        return f"{self.origin} → {self.destination}"


class BusType(models.TextChoices):
    AC = "ac", "AC"
    NON_AC = "non_ac", "Non AC"
    SLEEPER = "sleeper", "Sleeper"
    HYUNDAI = "hyundai", "Hyundai"


class Transport(models.Model):
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name="transports"
    )
    kind = models.CharField(max_length=10, choices=TransportKind.choices)
    bus_type = models.CharField(
        max_length=20, choices=BusType.choices, blank=True,
        help_text="Only used when kind = bus",
    )
    code = models.CharField(max_length=64, unique=True, blank=True)
    name = models.CharField(max_length=120, help_text="e.g. Volvo AC, Sundarban Express")
    registration_no = models.CharField(max_length=60, blank=True)
    total_seats = models.PositiveIntegerField(default=40)
    seats_per_row = models.PositiveIntegerField(default=4)
    has_vip_section = models.BooleanField(default=False)
    image = models.ImageField(upload_to="transports/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.code:
            count = Transport.objects.filter(provider=self.provider).count() + 1
            self.code = f"{self.provider.provider_code}_{self.kind}{count:02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Schedule(models.Model):
    transport = models.ForeignKey(
        Transport, on_delete=models.CASCADE, related_name="schedules"
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="schedules")
    driver = models.ForeignKey(
        DriverProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="schedules"
    )
    departure = models.DateTimeField()
    arrival = models.DateTimeField()
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    vip_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    series_id = models.CharField(
        max_length=32, blank=True, db_index=True,
        help_text="Shared across all schedules from one recurring publish",
    )
    status = models.CharField(
        max_length=20,
        default="scheduled",
        choices=[
            ("scheduled", "Scheduled"),
            ("boarding", "Boarding"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["departure"]

    def __str__(self):
        return f"{self.transport.code} {self.route} @ {self.departure:%Y-%m-%d %H:%M}"

    @property
    def duration(self):
        return self.arrival - self.departure

    @property
    def seats_booked_count(self):
        from apps.bookings.models import BookedSeat
        return BookedSeat.objects.filter(
            booking__schedule=self,
            booking__status__in=["confirmed", "boarded"],
        ).count()

    @property
    def seats_available(self):
        return self.transport.total_seats - self.seats_booked_count

    @property
    def occupancy_pct(self):
        if not self.transport.total_seats:
            return 0
        return round(self.seats_booked_count * 100 / self.transport.total_seats)
