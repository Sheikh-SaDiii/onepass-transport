import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.bookings.models import Booking
from apps.payments.models import Transaction


@login_required
@role_required("admin", "provider")
def index(request):
    return render(request, "reports/index.html")


@login_required
@role_required("admin", "provider")
def bookings_excel(request):
    from openpyxl import Workbook

    qs = Booking.objects.select_related("user", "schedule__transport", "schedule__route")
    if request.user.is_provider:
        qs = qs.filter(schedule__transport__provider=request.user.provider_profile)

    wb = Workbook()
    ws = wb.active
    ws.title = "Bookings"
    ws.append(["PNR", "Passenger", "Transport", "Route", "Departure", "Amount", "Status"])
    for b in qs:
        ws.append([
            b.pnr,
            b.user.get_full_name() or b.user.username,
            b.schedule.transport.code,
            f"{b.schedule.route.origin} → {b.schedule.route.destination}",
            b.schedule.departure.strftime("%Y-%m-%d %H:%M"),
            float(b.total_amount),
            b.status,
        ])
    buf = io.BytesIO()
    wb.save(buf)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="bookings_{timezone.now():%Y%m%d}.xlsx"'
    return resp


@login_required
@role_required("admin", "provider")
def revenue_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    qs = Transaction.objects.filter(kind="debit").select_related("user", "booking")
    if request.user.is_provider:
        qs = qs.filter(booking__schedule__transport__provider=request.user.provider_profile)

    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 50, "OnePass — Revenue Report")
    p.setFont("Helvetica", 9)
    p.drawString(40, height - 65, f"Generated {timezone.now():%Y-%m-%d %H:%M}")

    y = height - 100
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "Date")
    p.drawString(140, y, "User")
    p.drawString(280, y, "Method")
    p.drawString(360, y, "Booking")
    p.drawString(440, y, "Amount")
    p.line(40, y - 4, width - 40, y - 4)
    y -= 18
    p.setFont("Helvetica", 9)
    total = 0
    for t in qs[:200]:
        if y < 60:
            p.showPage()
            y = height - 60
        p.drawString(40, y, t.created_at.strftime("%Y-%m-%d"))
        p.drawString(140, y, (t.user.username or "")[:20])
        p.drawString(280, y, t.method)
        p.drawString(360, y, (t.booking.pnr if t.booking else "—"))
        p.drawRightString(width - 40, y, f"{t.amount}")
        total += float(t.amount)
        y -= 14
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y - 10, f"Total: ৳{total:,.2f}")
    p.showPage()
    p.save()

    resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="revenue_{timezone.now():%Y%m%d}.pdf"'
    return resp
