from datetime import datetime, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.accounts.decorators import role_required
from apps.accounts.models import TransportKind
from .models import Route, Transport, Schedule


# Dhaka MRT Line 6 — north → south
METRO_STATIONS = [
    "Uttara North", "Uttara Center", "Uttara South", "Pallabi",
    "Mirpur 11", "Mirpur 10", "Kazipara", "Shewrapara",
    "Agargaon", "Bijoy Sarani", "Farmgate", "Karwan Bazar",
    "Shahbag", "Dhaka University", "Bangladesh Secretariat", "Motijheel",
]
# All 64 Bangladesh districts + tourist destinations
CITIES = [
    # Dhaka division
    "Dhaka", "Faridpur", "Gazipur", "Gopalganj", "Kishoreganj", "Madaripur",
    "Manikganj", "Munshiganj", "Narayanganj", "Narsingdi", "Rajbari",
    "Shariatpur", "Tangail",
    # Chittagong division
    "Chittagong", "Bandarban", "Brahmanbaria", "Chandpur", "Comilla",
    "Cox's Bazar", "Feni", "Khagrachhari", "Lakshmipur", "Noakhali", "Rangamati",
    # Khulna division
    "Khulna", "Bagerhat", "Chuadanga", "Jessore", "Jhenaidah", "Kushtia",
    "Magura", "Meherpur", "Narail", "Satkhira",
    # Rajshahi division
    "Rajshahi", "Bogura", "Chapainawabganj", "Joypurhat", "Naogaon", "Natore",
    "Pabna", "Sirajganj",
    # Rangpur division
    "Rangpur", "Dinajpur", "Gaibandha", "Kurigram", "Lalmonirhat",
    "Nilphamari", "Panchagarh", "Thakurgaon",
    # Barisal division
    "Barisal", "Barguna", "Bhola", "Jhalokati", "Patuakhali", "Pirojpur",
    # Sylhet division
    "Sylhet", "Habiganj", "Moulvibazar", "Sunamganj",
    # Mymensingh division
    "Mymensingh", "Jamalpur", "Netrokona", "Sherpur",
    # Tourist destinations
    "Saint Martin's Island", "Sundarbans", "Kuakata", "Sajek Valley",
    "Sreemangal", "Bandarban Hill", "Teknaf", "Inani Beach",
]


def home(request):
    popular = Route.objects.all()[:8]
    stats = {
        "transports": Transport.objects.filter(is_active=True).count(),
        "providers": Transport.objects.values("provider").distinct().count(),
        "routes": Route.objects.count(),
        "schedules_today": Schedule.objects.filter(departure__date=timezone.now().date()).count(),
    }
    return render(
        request,
        "home.html",
        {
            "popular": popular,
            "stats": stats,
            "kinds": TransportKind.choices,
            "metro_stations": METRO_STATIONS,
            "cities": CITIES,
        },
    )


def search(request):
    kind = request.GET.get("kind", "bus")
    origin = (request.GET.get("origin") or "").strip()
    destination = (request.GET.get("destination") or "").strip()
    date_str = request.GET.get("date", "")
    date = parse_date(date_str) if date_str else timezone.now().date()

    if kind == "metro":
        results = _metro_results(origin, destination, date)
        suggestions = []
    else:
        qs = Schedule.objects.select_related("transport", "transport__provider", "route").filter(
            transport__kind=kind,
            transport__is_active=True,
            status__in=["scheduled", "boarding"],
        )
        if origin:
            qs = qs.filter(route__origin__icontains=origin)
        if destination:
            qs = qs.filter(route__destination__icontains=destination)
        if date:
            qs = qs.filter(departure__date=date)
        results = qs

        # If no results, look for the same route on other dates as a hint
        suggestions = []
        if origin and destination and not results.exists():
            other_dates = (
                Schedule.objects.filter(
                    transport__kind=kind,
                    transport__is_active=True,
                    route__origin__icontains=origin,
                    route__destination__icontains=destination,
                    departure__gte=timezone.now(),
                )
                .order_by("departure")
                .values_list("departure__date", flat=True)
                .distinct()[:6]
            )
            suggestions = list(other_dates)

    return render(
        request,
        "transports/search_results.html",
        {
            "results": results,
            "kind": kind,
            "origin": origin,
            "destination": destination,
            "date": date,
            "suggestions": suggestions,
            "kinds": TransportKind.choices,
            "metro_stations": METRO_STATIONS,
            "cities": CITIES,
            "is_metro": kind == "metro",
        },
    )


def _metro_results(origin, destination, date):
    """Metro Line 6 runs a fixed timetable every day: trains every 30 min from
    08:00 to 22:00. Materialize Schedule rows on demand for the queried pair so
    the search works for any future date without depending on pre-seeded data."""
    if not origin or not destination or origin == destination:
        return []
    if origin not in METRO_STATIONS or destination not in METRO_STATIONS:
        return []

    o_idx = METRO_STATIONS.index(origin)
    d_idx = METRO_STATIONS.index(destination)
    stops_between = abs(d_idx - o_idx)
    duration_min = stops_between * 3 + 2
    fare = max(20, min(100, stops_between * 10))

    metro_transports = list(
        Transport.objects.select_related("provider").filter(
            kind="metro", is_active=True
        ).order_by("id")
    )
    if not metro_transports:
        return []

    route, _ = Route.objects.get_or_create(
        origin=origin, destination=destination,
        defaults={"distance_km": stops_between * 2},
    )

    tz = timezone.get_current_timezone()
    base = timezone.make_aware(datetime.combine(date, time(hour=8)), tz)
    results = []
    for half in range(28):  # 14 hours x 2 departures/hour
        departure = base + timedelta(minutes=30 * half)
        transport = metro_transports[half % len(metro_transports)]
        sched, _ = Schedule.objects.get_or_create(
            transport=transport,
            route=route,
            departure=departure,
            defaults={
                "arrival": departure + timedelta(minutes=duration_min),
                "fare": fare,
                "vip_fare": 0,
            },
        )
        if sched.status in ("scheduled", "boarding"):
            results.append(sched)
    return results


@login_required
@role_required("provider")
def manage_transports(request):
    profile = request.user.provider_profile
    transports = profile.transports.all()
    return render(
        request,
        "transports/manage.html",
        {"transports": transports, "profile": profile},
    )


@login_required
@role_required("provider")
def delete_transport(request, pk):
    profile = request.user.provider_profile
    transport = get_object_or_404(Transport, pk=pk, provider=profile)
    if request.method != "POST":
        return redirect("transports:manage")
    name = transport.name
    schedule_count = transport.schedules.count()
    transport.delete()
    if schedule_count:
        messages.success(
            request, f"Deleted '{name}' and {schedule_count} associated schedule(s)."
        )
    else:
        messages.success(request, f"Deleted '{name}'.")
    return redirect("transports:manage")


@login_required
@role_required("provider")
def delete_series(request, series_id):
    profile = request.user.provider_profile
    if request.method != "POST":
        return redirect("dashboard:home")
    qs = Schedule.objects.filter(transport__provider=profile, series_id=series_id)
    n = qs.count()
    if n == 0:
        messages.error(request, "Series not found.")
        return redirect("dashboard:home")
    qs.delete()
    messages.success(request, f"Deleted recurring series ({n} schedules).")
    return redirect("dashboard:home")


@login_required
@role_required("provider")
def delete_all_schedules(request):
    profile = request.user.provider_profile
    if request.method != "POST":
        return redirect("dashboard:home")
    qs = Schedule.objects.filter(transport__provider=profile)
    n = qs.count()
    qs.delete()
    messages.success(request, f"Deleted all {n} schedule(s).")
    return redirect("dashboard:home")


@login_required
@role_required("provider")
def delete_schedule(request, pk):
    profile = request.user.provider_profile
    schedule = get_object_or_404(
        Schedule.objects.select_related("route", "transport"),
        pk=pk, transport__provider=profile,
    )
    if request.method != "POST":
        return redirect("dashboard:home")
    booking_count = schedule.bookings.exclude(status__in=["cancelled", "refunded"]).count()
    label = f"{schedule.route} on {schedule.departure:%b %d, %H:%M}"
    schedule.delete()
    if booking_count:
        messages.warning(
            request,
            f"Deleted schedule '{label}' along with {booking_count} active booking(s). "
            "Affected passengers should be notified.",
        )
    else:
        messages.success(request, f"Deleted schedule '{label}'.")
    return redirect("dashboard:home")


@login_required
@role_required("provider")
def add_transport(request):
    profile = request.user.provider_profile
    if request.method == "POST":
        Transport.objects.create(
            provider=profile,
            kind=profile.transport_kind,
            bus_type=request.POST.get("bus_type", "") if profile.transport_kind == "bus" else "",
            name=request.POST["name"],
            registration_no=request.POST.get("registration_no", ""),
            total_seats=int(request.POST.get("total_seats", 40)),
            seats_per_row=int(request.POST.get("seats_per_row", 4)),
            has_vip_section=bool(request.POST.get("has_vip_section")),
            image=request.FILES.get("image"),
        )
        messages.success(request, "Transport added.")
        return redirect("transports:manage")
    from .models import BusType
    return render(
        request,
        "transports/add_transport.html",
        {"profile": profile, "bus_types": BusType.choices},
    )


@login_required
@role_required("provider")
def add_schedule(request):
    profile = request.user.provider_profile
    if request.method == "POST":
        from django.utils.dateparse import parse_datetime
        # Normalize city names: strip + title-case so "DHAKA", "dhaka", " Dhaka "
        # all become "Dhaka" — keeps the DB clean and matches case-insensitively.
        origin = request.POST["origin"].strip().title()
        destination = request.POST["destination"].strip().title()
        # Reuse an existing route with the same name regardless of case
        route = (
            Route.objects.filter(origin__iexact=origin, destination__iexact=destination).first()
            or Route.objects.create(
                origin=origin,
                destination=destination,
                distance_km=int(request.POST.get("distance_km") or 0),
            )
        )
        transport_id = int(request.POST["transport"])
        fare = request.POST["fare"]
        vip_fare = request.POST.get("vip_fare") or 0
        repeat_daily = bool(request.POST.get("repeat_daily"))

        if repeat_daily:
            # Time-only mode: combine today's date with the chosen times
            dep_time_str = request.POST.get("departure_time", "")
            arr_time_str = request.POST.get("arrival_time", "")
            if not dep_time_str or not arr_time_str:
                messages.error(request, "Set both departure time and arrival time.")
                return redirect("transports:add_schedule")
            try:
                dh, dm = map(int, dep_time_str.split(":"))
                ah, am = map(int, arr_time_str.split(":"))
            except ValueError:
                messages.error(request, "Invalid time format.")
                return redirect("transports:add_schedule")
            today = timezone.localtime(timezone.now())
            dep_dt = today.replace(hour=dh, minute=dm, second=0, microsecond=0)
            arr_dt = today.replace(hour=ah, minute=am, second=0, microsecond=0)
            # overnight trip — arrival is next day
            if arr_dt <= dep_dt:
                arr_dt += timedelta(days=1)
        else:
            dep_dt = parse_datetime(request.POST["departure"])
            arr_dt = parse_datetime(request.POST["arrival"])
            if dep_dt is None or arr_dt is None:
                messages.error(request, "Invalid departure or arrival datetime.")
                return redirect("transports:add_schedule")

        try:
            repeat_days = int(request.POST.get("repeat_days") or 1)
        except ValueError:
            repeat_days = 1
        repeat_days = max(1, min(90, repeat_days)) if repeat_daily else 1

        import uuid
        series = uuid.uuid4().hex[:16] if (repeat_daily and repeat_days > 1) else ""

        first = None
        created = 0
        for offset in range(repeat_days):
            s = Schedule.objects.create(
                transport_id=transport_id,
                route=route,
                departure=dep_dt + timedelta(days=offset),
                arrival=arr_dt + timedelta(days=offset),
                fare=fare,
                vip_fare=vip_fare,
                series_id=series,
            )
            if first is None:
                first = s
            created += 1

        first.refresh_from_db()
        if created == 1:
            messages.success(
                request,
                f"Schedule published: {first.route} on {first.departure:%b %d, %H:%M}. "
                "See it on your dashboard below.",
            )
        else:
            messages.success(
                request,
                f"Published {created} daily schedules: {first.route} at "
                f"{first.departure:%H:%M} starting {first.departure:%b %d} "
                f"for the next {created} days.",
            )
        return redirect("dashboard:home")
    from .models import BusType
    return render(
        request,
        "transports/add_schedule.html",
        {
            "transports": profile.transports.filter(is_active=True),
            "is_bus_provider": profile.transport_kind == "bus",
            "bus_types": BusType.choices,
            "cities": CITIES,
            "metro_stations": METRO_STATIONS,
        },
    )
