from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.transports.models import Schedule
from apps.payments.models import Transaction, Wallet
from apps.qr_system.utils import generate_qr_for_booking
from .models import Booking, BookedSeat


@login_required
def select_seats(request, schedule_id):
    schedule = get_object_or_404(
        Schedule.objects.select_related("transport", "route", "transport__provider"),
        pk=schedule_id,
    )

    # Metro: no seat assignment — just pick passenger count and pay
    if schedule.transport.kind == "metro":
        return render(request, "bookings/metro_select.html", {"schedule": schedule})

    booked = list(
        BookedSeat.objects.filter(
            booking__schedule=schedule,
            booking__status__in=["confirmed", "boarded", "pending"],
        ).values_list("seat_number", flat=True)
    )

    rows = []
    per_row = schedule.transport.seats_per_row
    total = schedule.transport.total_seats
    n = 1
    while n <= total:
        rows.append([f"{n+i}" for i in range(per_row) if n + i <= total])
        n += per_row

    return render(
        request,
        "bookings/seat_select.html",
        {
            "schedule": schedule,
            "rows": rows,
            "booked": booked,
            "vip_rows": rows[:1] if schedule.transport.has_vip_section else [],
        },
    )


@login_required
@transaction.atomic
def create_booking(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)

    # Metro: ride-only, no seat assignment
    if schedule.transport.kind == "metro":
        try:
            passengers = int(request.POST.get("passengers", 1) or 1)
        except ValueError:
            passengers = 1
        passengers = max(1, min(50, passengers))
        total = schedule.fare * passengers
        booking = Booking.objects.create(user=request.user, schedule=schedule, total_amount=total)
        for i in range(passengers):
            BookedSeat.objects.create(booking=booking, seat_number=f"P{i + 1}")
        return redirect("bookings:checkout", pnr=booking.pnr)

    seat_csv = request.POST.get("seats", "")
    seats = [s.strip() for s in seat_csv.split(",") if s.strip()]
    if not seats:
        messages.error(request, "Pick at least one seat.")
        return redirect("bookings:select_seats", schedule_id=schedule.id)

    already = set(
        BookedSeat.objects.filter(
            booking__schedule=schedule,
            booking__status__in=["confirmed", "boarded", "pending"],
            seat_number__in=seats,
        ).values_list("seat_number", flat=True)
    )
    if already:
        messages.error(request, f"Seats already taken: {', '.join(sorted(already))}")
        return redirect("bookings:select_seats", schedule_id=schedule.id)

    vip_seats = set()
    if schedule.transport.has_vip_section:
        vip_seats = {s for s in seats if int(s) <= schedule.transport.seats_per_row}

    total = Decimal("0.00")
    for s in seats:
        total += schedule.vip_fare if s in vip_seats else schedule.fare

    booking = Booking.objects.create(user=request.user, schedule=schedule, total_amount=total)
    for s in seats:
        BookedSeat.objects.create(booking=booking, seat_number=s, is_vip=(s in vip_seats))

    return redirect("bookings:checkout", pnr=booking.pnr)


@login_required
def checkout(request, pnr):
    booking = get_object_or_404(Booking, pnr=pnr, user=request.user)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    return render(request, "bookings/checkout.html", {"booking": booking, "wallet": wallet})


@login_required
@transaction.atomic
def pay(request, pnr):
    booking = get_object_or_404(Booking, pnr=pnr, user=request.user)
    if booking.status != "pending":
        messages.info(request, "Booking already processed.")
        return redirect("bookings:ticket", pnr=pnr)

    method = request.POST.get("method", "wallet")
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if method == "wallet":
        if wallet.balance < booking.total_amount:
            messages.error(request, "Not enough wallet balance. Add funds first.")
            return redirect("payments:wallet")
        wallet.balance -= booking.total_amount
        wallet.save()
        Transaction.objects.create(
            user=request.user,
            booking=booking,
            amount=booking.total_amount,
            kind="debit",
            method="wallet",
            note=f"Booking {booking.pnr}",
        )
    else:  # simulated card / mobile banking
        Transaction.objects.create(
            user=request.user,
            booking=booking,
            amount=booking.total_amount,
            kind="debit",
            method=method,
            note=f"Booking {booking.pnr} ({method})",
        )

    booking.status = "confirmed"
    generate_qr_for_booking(booking)
    booking.save()
    messages.success(request, f"Booking confirmed. PNR {booking.pnr}")
    return redirect("bookings:ticket", pnr=pnr)


@login_required
def ticket(request, pnr):
    booking = get_object_or_404(
        Booking.objects.select_related("schedule__transport", "schedule__route"),
        pnr=pnr,
        user=request.user,
    )
    return render(request, "bookings/ticket.html", {"booking": booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related(
        "schedule__transport", "schedule__route"
    )
    return render(request, "bookings/my_bookings.html", {"bookings": bookings})


@login_required
def invoice(request, pnr):
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from django.http import HttpResponse

    booking = get_object_or_404(
        Booking.objects.select_related("schedule__transport", "schedule__route", "user"),
        pnr=pnr,
    )
    if booking.user_id != request.user.id and not request.user.is_superuser \
            and not (request.user.is_provider and booking.schedule.transport.provider.user_id == request.user.id):
        return redirect("dashboard:home")

    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Header
    p.setFillColorRGB(0.91, 0.24, 0.24)
    p.rect(0, height - 70, width, 70, fill=1, stroke=0)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, height - 45, "OnePass")
    p.setFont("Helvetica", 11)
    p.drawString(40, height - 60, "Tax invoice / Booking receipt")
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(width - 40, height - 38, f"PNR  {booking.pnr}")
    p.setFont("Helvetica", 9)
    p.drawRightString(width - 40, height - 55, f"Issued {booking.created_at:%Y-%m-%d %H:%M}")

    # Body
    p.setFillColorRGB(0, 0, 0)
    y = height - 110
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Passenger")
    p.drawString(300, y, "Operator")
    p.setFont("Helvetica", 10)
    p.drawString(40, y - 14, booking.user.get_full_name() or booking.user.username)
    p.drawString(40, y - 28, booking.user.email)
    p.drawString(300, y - 14, booking.schedule.transport.provider.company_name)
    p.drawString(300, y - 28, booking.schedule.transport.code)

    y -= 70
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Journey")
    p.setFont("Helvetica", 10)
    y -= 16
    p.drawString(40, y, f"Route:    {booking.schedule.route.origin}  ->  {booking.schedule.route.destination}")
    y -= 14
    p.drawString(40, y, f"Transport: {booking.schedule.transport.name} ({booking.schedule.transport.get_kind_display()})")
    y -= 14
    p.drawString(40, y, f"Departure: {booking.schedule.departure:%Y-%m-%d %H:%M}")
    y -= 14
    p.drawString(40, y, f"Arrival:   {booking.schedule.arrival:%Y-%m-%d %H:%M}")
    y -= 14
    seats = ", ".join([s.seat_number for s in booking.seats.all()])
    p.drawString(40, y, f"Seats:     {seats}")

    y -= 30
    p.setStrokeColorRGB(.85, .85, .85)
    p.line(40, y, width - 40, y)
    y -= 22
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Total Paid")
    p.drawRightString(width - 40, y, f"BDT {booking.total_amount}")
    y -= 18
    p.setFont("Helvetica", 9)
    p.setFillColorRGB(.4, .4, .4)
    p.drawString(40, y, f"Status: {booking.get_status_display()}")

    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width / 2, 30, "OnePass — One pass for every journey. This is a system-generated invoice.")

    p.showPage()
    p.save()
    resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="invoice_{booking.pnr}.pdf"'
    return resp


@login_required
def cancel_booking(request, pnr):
    booking = get_object_or_404(Booking, pnr=pnr, user=request.user)
    if booking.status != "confirmed":
        messages.error(request, "Cannot cancel this booking.")
        return redirect("bookings:my_bookings")
    booking.status = "refunded"
    booking.save()
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += booking.total_amount
    wallet.save()
    Transaction.objects.create(
        user=request.user,
        booking=booking,
        amount=booking.total_amount,
        kind="credit",
        method="refund",
        note=f"Refund {booking.pnr}",
    )
    messages.success(request, "Booking cancelled and refunded to wallet.")
    return redirect("bookings:my_bookings")
