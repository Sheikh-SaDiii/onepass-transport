from decimal import Decimal
from django.conf import settings
from django.db import models


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} — ৳{self.balance}"


class Transaction(models.Model):
    KIND = [("credit", "Credit"), ("debit", "Debit")]
    METHOD = [
        ("wallet", "Wallet"),
        ("card", "Card"),
        ("bkash", "bKash"),
        ("nagad", "Nagad"),
        ("rocket", "Rocket"),
        ("bank", "Bank"),
        ("topup", "Top-up"),
        ("refund", "Refund"),
        ("settlement", "Settlement"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    kind = models.CharField(max_length=10, choices=KIND)
    method = models.CharField(max_length=20, choices=METHOD)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind} ৳{self.amount} via {self.method}"
