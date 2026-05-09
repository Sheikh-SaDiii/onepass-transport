from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.accounts.models import User, Role, ProviderProfile, TransportKind
from apps.transports.models import Route, Transport, Schedule
from apps.payments.models import Wallet


class Command(BaseCommand):
    help = "Seed demo data: users, providers, drivers, transports, schedules."

    @transaction.atomic
    def handle(self, *args, **opts):
        self.stdout.write("Seeding demo data…")

        # ---------- Admin ----------
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@onepass.local",
                "first_name": "Admin",
                "last_name": "User",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("admin12345")
        admin.role = Role.ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        # ---------- Sample user ----------
        user, _ = User.objects.get_or_create(
            username="user1",
            defaults={
                "email": "user@onepass.local",
                "first_name": "Rahim",
                "last_name": "Ahmed",
                "role": Role.USER,
                "wallet_balance": Decimal("5000.00"),
            },
        )
        user.set_password("user12345")
        user.save()
        Wallet.objects.get_or_create(user=user, defaults={"balance": Decimal("5000.00")})

        # ---------- Providers (one per kind) ----------
        provider_specs = [
            ("greenline", "Green Line Paribahan", TransportKind.BUS),
            ("sundarban", "Sundarban Express", TransportKind.TRAIN),
            ("biman", "Biman Bangladesh Airlines", TransportKind.PLANE),
            ("rocket", "Rocket Service", TransportKind.SHIP),
        ]
        provider_profiles = {}
        for username, company, kind in provider_specs:
            pu, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@onepass.local",
                    "first_name": company.split()[0],
                    "role": Role.PROVIDER,
                },
            )
            pu.set_password("provider123")
            pu.role = Role.PROVIDER
            pu.is_approved = True   # seeded providers are pre-approved for demo
            pu.save()
            pp, _ = ProviderProfile.objects.get_or_create(
                user=pu,
                defaults={"company_name": company, "transport_kind": kind},
            )
            provider_profiles[kind] = pp

        # also a friendly "provider" alias account
        prov_alias, _ = User.objects.get_or_create(
            username="provider",
            defaults={
                "email": "provider@onepass.local",
                "first_name": "Provider",
                "role": Role.PROVIDER,
            },
        )
        prov_alias.set_password("provider123")
        prov_alias.role = Role.PROVIDER
        prov_alias.is_approved = True
        prov_alias.save()
        ProviderProfile.objects.get_or_create(
            user=prov_alias,
            defaults={"company_name": "Demo Travels", "transport_kind": TransportKind.BUS},
        )

        # ---------- Sample pending provider (so admin sees approval queue) ----------
        pending_user, _ = User.objects.get_or_create(
            username="newprovider",
            defaults={
                "email": "newprovider@onepass.local",
                "first_name": "Pending",
                "last_name": "Applicant",
                "role": Role.PROVIDER,
            },
        )
        pending_user.set_password("provider123")
        pending_user.role = Role.PROVIDER
        pending_user.is_approved = False
        pending_user.save()
        ProviderProfile.objects.get_or_create(
            user=pending_user,
            defaults={
                "company_name": "Hanif Enterprise (Pending)",
                "transport_kind": TransportKind.BUS,
            },
        )

        # Clean up legacy driver login from earlier schema (3-role model now)
        User.objects.filter(username="driver").delete()

        # ---------- Routes ----------
        routes_data = [
            ("Dhaka", "Cox's Bazar", 414),
            ("Dhaka", "Chittagong", 264),
            ("Dhaka", "Sylhet", 247),
            ("Dhaka", "Khulna", 271),
            ("Dhaka", "Rajshahi", 256),
            ("Dhaka", "Barisal", 173),
            ("Chittagong", "Cox's Bazar", 152),
            ("Dhaka", "Rangpur", 304),
        ]
        routes = {}
        for o, d, km in routes_data:
            r, _ = Route.objects.get_or_create(origin=o, destination=d, defaults={"distance_km": km})
            routes[(o, d)] = r

        # ---------- Transports + schedules ----------
        fleet = [
            (TransportKind.BUS, "Volvo AC 9700", 36, 4, True),
            (TransportKind.BUS, "Hyundai Universe", 40, 4, False),
            (TransportKind.TRAIN, "Sundarban Express", 120, 6, True),
            (TransportKind.PLANE, "Biman 737", 158, 6, True),
            (TransportKind.SHIP, "MV Sundarban-10", 200, 8, False),
        ]
        now = timezone.now()
        for idx, (kind, name, seats, per_row, vip) in enumerate(fleet):
            provider = provider_profiles[kind]
            t, _ = Transport.objects.get_or_create(
                provider=provider,
                name=name,
                defaults={
                    "kind": kind,
                    "total_seats": seats,
                    "seats_per_row": per_row,
                    "has_vip_section": vip,
                },
            )
            # 3 schedules each across the next 3 days
            for day in range(3):
                for j, (route_key, hour, fare) in enumerate([
                    (("Dhaka", "Cox's Bazar"), 8, 1500),
                    (("Dhaka", "Chittagong"), 14, 1200),
                    (("Dhaka", "Sylhet"), 22, 1000),
                ]):
                    departure = (now + timedelta(days=day)).replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    )
                    arrival = departure + timedelta(hours=6 + j)
                    Schedule.objects.get_or_create(
                        transport=t,
                        route=routes[route_key],
                        departure=departure,
                        defaults={
                            "arrival": arrival,
                            "fare": Decimal(fare + idx * 100),
                            "vip_fare": Decimal(fare + 500 + idx * 100),
                        },
                    )

        # ---------- Dhaka MRT (Bangladesh Metro Rail) ----------
        mrt_user, _ = User.objects.get_or_create(
            username="dmtcl",
            defaults={
                "email": "dmtcl@onepass.local",
                "first_name": "Dhaka MRT",
                "role": Role.PROVIDER,
            },
        )
        mrt_user.set_password("provider123")
        mrt_user.role = Role.PROVIDER
        mrt_user.is_approved = True
        mrt_user.save()
        mrt_provider, _ = ProviderProfile.objects.get_or_create(
            user=mrt_user,
            defaults={
                "company_name": "Dhaka Mass Transit Company (DMTCL)",
                "transport_kind": TransportKind.METRO,
            },
        )

        # MRT Line 6 — common origin/destination pairs across the 16-station line
        # (Uttara North, Uttara Center, Uttara South, Pallabi, Mirpur 11, Mirpur 10,
        #  Kazipara, Shewrapara, Agargaon, Bijoy Sarani, Farmgate, Karwan Bazar,
        #  Shahbag, Dhaka University, Bangladesh Secretariat, Motijheel)
        mrt_pairs = [
            ("Uttara North", "Motijheel", 21, 100),
            ("Uttara North", "Agargaon", 11, 60),
            ("Uttara North", "Farmgate", 14, 80),
            ("Mirpur 10", "Motijheel", 13, 70),
            ("Agargaon", "Motijheel", 10, 60),
            ("Farmgate", "Motijheel", 7, 30),
            ("Uttara South", "Shahbag", 16, 80),
        ]
        for o, d, km, fare in mrt_pairs:
            r, _ = Route.objects.get_or_create(
                origin=o, destination=d, defaults={"distance_km": km}
            )
        # Two MRT trainsets
        mrt_trains = [
            ("MRT Line 6 — Set A (Kawasaki)", 600, 6),
            ("MRT Line 6 — Set B (Kawasaki)", 600, 6),
        ]
        for name, seats, per_row in mrt_trains:
            t, _ = Transport.objects.get_or_create(
                provider=mrt_provider,
                name=name,
                defaults={
                    "kind": TransportKind.METRO,
                    "total_seats": seats,
                    "seats_per_row": per_row,
                    "has_vip_section": False,
                },
            )
            # Frequent service: every 30 min for next 3 days, 8am–10pm
            for day in range(3):
                base_day = (now + timedelta(days=day)).replace(
                    hour=8, minute=0, second=0, microsecond=0
                )
                for half in range(0, 28):  # 14 hours x 2
                    departure = base_day + timedelta(minutes=30 * half)
                    for o, d, km, fare in mrt_pairs[:3]:
                        route = Route.objects.get(origin=o, destination=d)
                        Schedule.objects.get_or_create(
                            transport=t,
                            route=route,
                            departure=departure,
                            defaults={
                                "arrival": departure + timedelta(minutes=max(15, km * 2)),
                                "fare": Decimal(fare),
                                "vip_fare": Decimal(0),
                            },
                        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write("")
        self.stdout.write("Demo accounts:")
        self.stdout.write("  admin       / admin12345    (full control + approval queue)")
        self.stdout.write("  provider    / provider123   (also: greenline, sundarban, biman, rocket, dmtcl)")
        self.stdout.write("  newprovider / provider123   (pending approval - try as admin)")
        self.stdout.write("  user1       / user12345     (5000 BDT wallet)")
