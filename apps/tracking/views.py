from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from apps.transports.models import Transport
from core import firebase
from .models import GPSPing


@login_required
def live(request, transport_id):
    transport = get_object_or_404(Transport, pk=transport_id)
    last = transport.pings.first()
    return render(
        request,
        "tracking/live.html",
        {"transport": transport, "last": last, "firebase": firebase.is_enabled()},
    )


@login_required
def push_ping(request, transport_id):
    transport = get_object_or_404(Transport, pk=transport_id)
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)
    try:
        lat = float(request.POST["lat"])
        lng = float(request.POST["lng"])
    except (KeyError, ValueError):
        return JsonResponse({"ok": False, "error": "lat/lng required"}, status=400)
    speed = float(request.POST.get("speed", 0))
    status = request.POST.get("status", "running")
    GPSPing.objects.create(transport=transport, lat=lat, lng=lng, speed_kmh=speed, status=status)
    firebase.push_gps(transport.code, lat, lng, status)
    return JsonResponse({"ok": True})


@login_required
def latest(request, transport_id):
    p = GPSPing.objects.filter(transport_id=transport_id).first()
    if not p:
        return JsonResponse({"ok": False})
    return JsonResponse({"ok": True, "lat": p.lat, "lng": p.lng, "status": p.status,
                         "speed": p.speed_kmh, "at": p.recorded_at.isoformat()})
