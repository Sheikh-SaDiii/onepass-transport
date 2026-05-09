from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import User, Role, ProviderProfile, DriverProfile
from apps.transports.models import Transport, Schedule, Route
from apps.bookings.models import Booking, BookedSeat
from apps.payments.models import Transaction


@login_required
def home(request):
    role = getattr(request.user, "role", None)
    if request.user.is_superuser or role == Role.ADMIN:
        return admin_dashboard(request)
    if role == Role.PROVIDER:
        if not request.user.is_approved:
            return render(request, "dashboard/awaiting_approval.html")
        return provider_dashboard(request)
    return user_dashboard(request)


def _last_n_days(n=7):
    today = timezone.now().date()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


def _last_n_months(n=6):
    today = timezone.now().date().replace(day=1)
    months = []
    for i in range(n - 1, -1, -1):
        # walk back i months
        m = today
        for _ in range(i):
            m = (m - timedelta(days=1)).replace(day=1)
        months.append(m)
    return months


def admin_dashboard(request):
    # 7-day series
    days = _last_n_days(7)
    revenue_per_day = []
    bookings_per_day = []
    for d in days:
        rev = Transaction.objects.filter(
            kind="debit", method__in=["wallet", "card", "bkash", "nagad", "rocket", "bank"],
            created_at__date=d,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        revenue_per_day.append(float(rev))
        bookings_per_day.append(Booking.objects.filter(created_at__date=d).count())

    # 6-month revenue series
    months = _last_n_months(6)
    monthly_revenue = []
    for m in months:
        next_m = (m + timedelta(days=32)).replace(day=1)
        rev = Transaction.objects.filter(
            kind="debit",
            created_at__date__gte=m,
            created_at__date__lt=next_m,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        monthly_revenue.append(float(rev))

    # User growth (cumulative per day)
    user_growth = []
    for d in days:
        user_growth.append(User.objects.filter(date_joined__date__lte=d).count())

    # Transports by kind (donut)
    by_kind = list(Transport.objects.values("kind").annotate(c=Count("id")).order_by("-c"))

    # Top providers by booking count
    provider_perf = (
        ProviderProfile.objects.annotate(
            total=Count("transports__schedules__bookings")
        ).order_by("-total")[:6]
    )

    # Most popular routes
    popular_routes = (
        Route.objects.annotate(c=Count("schedules__bookings")).order_by("-c")[:5]
    )

    # Payment methods breakdown
    pay_methods = list(
        Transaction.objects.filter(kind="debit")
        .values("method").annotate(c=Count("id")).order_by("-c")
    )

    # Seat occupancy
    seats_total = sum(t.total_seats for t in Transport.objects.all())
    seats_booked = BookedSeat.objects.filter(
        booking__status__in=["confirmed", "boarded"]
    ).count()
    occupancy_pct = round(seats_booked * 100 / seats_total) if seats_total else 0

    ctx = {
        "users_total": User.objects.count(),
        "providers_total": ProviderProfile.objects.count(),
        "providers_pending": User.objects.filter(role=Role.PROVIDER, is_approved=False).count(),
        "drivers_total": DriverProfile.objects.count(),
        "transports_total": Transport.objects.count(),
        "bookings_total": Booking.objects.count(),
        "transactions_total": Transaction.objects.count(),
        "revenue_total": Transaction.objects.filter(kind="debit").aggregate(s=Sum("amount"))["s"] or 0,
        "active_routes": Route.objects.filter(schedules__departure__gte=timezone.now()).distinct().count(),
        "occupancy_pct": occupancy_pct,
        "labels": [d.strftime("%b %d") for d in days],
        "revenue_series": revenue_per_day,
        "bookings_series": bookings_per_day,
        "user_growth_series": user_growth,
        "month_labels": [m.strftime("%b") for m in months],
        "monthly_revenue": monthly_revenue,
        "by_kind": by_kind,
        "provider_perf": provider_perf,
        "popular_routes": popular_routes,
        "pay_methods": pay_methods,
        "recent_bookings": Booking.objects.select_related("user", "schedule__transport")[:8],
    }
    return render(request, "dashboard/admin.html", ctx)


def provider_dashboard(request):
    profile = getattr(request.user, "provider_profile", None)
    if profile is None:
        return render(request, "dashboard/provider_setup.html")

    schedules = Schedule.objects.filter(transport__provider=profile)
    bookings = Booking.objects.filter(schedule__transport__provider=profile)
    revenue = Transaction.objects.filter(
        booking__schedule__transport__provider=profile, kind="debit"
    ).aggregate(s=Sum("amount"))["s"] or 0
    seats_booked = BookedSeat.objects.filter(
        booking__schedule__transport__provider=profile,
        booking__status__in=["confirmed", "boarded"],
    ).count()
    seats_total = sum(t.total_seats for t in profile.transports.all())
    occupancy = round(seats_booked * 100 / seats_total) if seats_total else 0

    upcoming = schedules.filter(departure__gte=timezone.now())

    # Group recently published by series_id so a "Repeat daily" publish shows
    # as a single row instead of N rows. Each group keeps the full list of its
    # schedules so the UI can offer per-day delete inside a dropdown.
    from collections import OrderedDict
    groups = OrderedDict()
    for s in schedules.order_by("-created_at")[:500]:
        key = s.series_id or f"_solo_{s.id}"
        if key not in groups:
            if len(groups) >= 5:
                continue  # already have 5 groups; ignore additional series
            groups[key] = {
                "first": s,
                "count": 0,
                "is_series": bool(s.series_id),
                "earliest_dep": s.departure,
                "latest_dep": s.departure,
                "series_id": s.series_id,
                "schedules": [],
            }
        g = groups[key]
        g["count"] += 1
        g["schedules"].append(s)
        if s.departure < g["earliest_dep"]:
            g["earliest_dep"] = s.departure
        if s.departure > g["latest_dep"]:
            g["latest_dep"] = s.departure
    # Sort each group's schedules chronologically (earliest first)
    for g in groups.values():
        g["schedules"].sort(key=lambda x: x.departure)
    schedules_recent_groups = list(groups.values())

    return render(
        request,
        "dashboard/provider.html",
        {
            "profile": profile,
            "transports": profile.transports.all(),
            "schedules_recent_groups": schedules_recent_groups,
            "schedules_upcoming": upcoming.order_by("departure")[:8],
            "schedules_total": schedules.count(),
            "schedules_upcoming_total": upcoming.count(),
            "bookings_recent": bookings.order_by("-created_at")[:8],
            "revenue": revenue,
            "occupancy": occupancy,
            "trips_active": schedules.filter(status="running").count(),
            "trips_cancelled": schedules.filter(status="cancelled").count(),
            "wallet_balance": getattr(request.user, "wallet_balance", 0),
        },
    )


def user_dashboard(request):
    bookings = Booking.objects.filter(user=request.user).select_related(
        "schedule__transport", "schedule__route"
    )
    upcoming = bookings.filter(
        status__in=["confirmed", "boarded"], schedule__departure__gte=timezone.now()
    )[:5]
    history = bookings.order_by("-created_at")[:8]
    return render(
        request,
        "dashboard/user.html",
        {
            "bookings_total": bookings.count(),
            "upcoming": upcoming,
            "history": history,
            "wallet_balance": getattr(request.user, "wallet_balance", 0),
        },
    )
