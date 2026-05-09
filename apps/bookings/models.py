import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.transports.models import Schedule


class Booking(models.Model):
    STATUS = [
        ("pending", "Pending Payment"),
        ("confirmed", "Confirmed"),
        ("boarded", "Boarded"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]
    pnr = models.CharField(max_length=12, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="bookings")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=15, choices=STATUS, default="pending")
    qr_token = models.CharField(max_length=64, unique=True, editable=False)
    qr_image = models.ImageField(upload_to="qr/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.pnr:
            self.pnr = uuid.uuid4().hex[:8].upper()
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PNR {self.pnr} — {self.user} — {self.schedule}"


class BookedSeat(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=8)
    is_vip = models.BooleanField(default=False)
    boarded = models.BooleanField(default=False)

    class Meta:
        unique_together = ("booking", "seat_number")

    def __str__(self):
        return f"{self.booking.pnr} · seat {self.seat_number}"
