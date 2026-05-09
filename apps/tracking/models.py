from django.db import models
from apps.transports.models import Transport


class GPSPing(models.Model):
    transport = models.ForeignKey(Transport, on_delete=models.CASCADE, related_name="pings")
    lat = models.FloatField()
    lng = models.FloatField()
    speed_kmh = models.FloatField(default=0)
    status = models.CharField(max_length=20, default="running")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.transport.code} @ {self.recorded_at:%H:%M:%S}"
