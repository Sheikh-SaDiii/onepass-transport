from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.bookings.models import Booking, BookedSeat


@login_required
@role_required("provider", "admin")
def scanner(request):
    return render(request, "qr_system/scanner.html")


@login_required
@role_required("provider", "admin")
def verify(request):
    token = request.GET.get("token", "") or request.POST.get("token", "")
    if "|" in token:
        # payload format: OnePass|PNR|qr_token
        parts = token.split("|")
        if len(parts) >= 3:
            token = parts[2]
    try:
        booking = Booking.objects.select_related("schedule__transport", "user").get(qr_token=token)
    except Booking.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid QR code"})

    if booking.status not in ("confirmed", "boarded"):
        return JsonResponse({"ok": False, "error": f"Booking is {booking.status}"})

    BookedSeat.objects.filter(booking=booking).update(boarded=True)
    booking.status = "boarded"
    booking.save()
    return JsonResponse({
        "ok": True,
        "pnr": booking.pnr,
        "passenger": booking.user.get_full_name() or booking.user.username,
        "transport": str(booking.schedule.transport),
        "seats": list(booking.seats.values_list("seat_number", flat=True)),
    })
