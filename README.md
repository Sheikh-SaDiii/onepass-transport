<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24&height=200&section=header&text=OnePass%20Transport&fontSize=56&fontAlignY=38&fontColor=ffffff&desc=One%20ticket%20%E2%80%A2%20Every%20ride&descSize=18&descAlignY=62&animation=fadeIn" alt="OnePass banner" />

<p>
  <img src="https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Firebase-Auth%20%2B%20Realtime-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" />
  <img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-Dev-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
</p>

<p>
  <img src="https://img.shields.io/github/last-commit/Sheikh-SaDiii/onepass-transport?style=flat-square&color=58a6ff" />
  <img src="https://img.shields.io/github/repo-size/Sheikh-SaDiii/onepass-transport?style=flat-square&color=58a6ff" />
  <img src="https://img.shields.io/github/languages/top/Sheikh-SaDiii/onepass-transport?style=flat-square&color=58a6ff" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" />
</p>

</div>

---

## Overview

**OnePass** is a unified Django + Firebase platform for booking **buses, trains, planes, and ships** from one interface. Four roles work in concert: **Admin**, **Service Provider**, **Driver**, and **User** — each with a dedicated dashboard.

> One account. Every mode of transport. Live tracking. QR ticketing. End-to-end booking lifecycle.

---

## Features

| Module | Capability |
|---|---|
| **Multi-modal booking** | Bus · Train · Plane · Ship — same flow |
| **Role-based dashboards** | Admin / Provider / Driver / User |
| **Auth** | Custom Django user + Firebase email/password |
| **Seat selection** | Interactive layout, lock-on-select |
| **QR ticketing** | Generate + scan + verify |
| **Live GPS tracking** | Firebase Realtime DB |
| **Payments** | Wallet, transactions, simulated gateway |
| **Notifications** | Email + Firebase Cloud Messaging |
| **Reports** | PDF (ReportLab) + Excel (openpyxl) exports |
| **Charts** | Chart.js dashboards |

---

## Tech Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=django,python,firebase,bootstrap,js,html,css,sqlite,git,github" />

</div>

`Django 5` · `Bootstrap 5` · `Chart.js` · `Firebase Admin SDK` · `qrcode` · `ReportLab` · `openpyxl`

---

## Quick Start

```bash
# 1. clone
git clone https://github.com/Sheikh-SaDiii/onepass-transport.git
cd onepass-transport

# 2. virtualenv
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate      # macOS / Linux

# 3. install deps
pip install -r requirements.txt

# 4. env
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
# edit .env with your secrets

# 5. database + seed
python manage.py migrate
python manage.py seed_demo      # demo users / providers / transports

# 6. run
python manage.py runserver
```

Open <http://127.0.0.1:8000>

---

## Demo Accounts

After running `seed_demo`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@onepass.local` | `admin12345` |
| Provider | `provider@onepass.local` | `provider123` |
| Driver | `driver@onepass.local` | `driver123` |
| User | `user@onepass.local` | `user12345` |

> Change these before any public deploy.

---

## Firebase Setup

1. Create a project at <https://console.firebase.google.com>
2. Enable: **Authentication** (Email/Password), **Firestore**, **Realtime Database**, **Storage**, **Cloud Messaging**
3. Project Settings → Service accounts → **Generate new private key** → save as `serviceAccountKey.json` in project root
4. Project Settings → General → copy web config values into `.env`

> The app runs **without** Firebase configured — falls back to local SQLite, dummy QR, and stub tracking. Real-time seat sync and live GPS activate once Firebase credentials are present.

---

## Project Layout

```
onepass-transport/
├── apps/
│   ├── accounts/        # custom user, 4 roles, profiles, auth, Firebase bridge
│   ├── transports/      # Bus / Train / Plane / Ship · routes · schedules
│   ├── bookings/        # seat selection, booking lifecycle
│   ├── payments/        # wallet, transactions, simulated gateway
│   ├── qr_system/       # QR generation + scan verification
│   ├── tracking/        # live GPS (Firebase Realtime DB)
│   ├── notifications/   # email + FCM push
│   ├── dashboard/       # role-based dashboards with charts
│   └── reports/         # PDF + Excel exports
├── core/                # shared firebase helpers
├── onepass/             # Django settings, urls, wsgi/asgi
├── templates/           # role-segmented HTML templates
├── static/              # css, js, autocomplete, firebase-init
├── manage.py
└── requirements.txt
```

---

## Apps at a Glance

| App | Purpose |
|-----|---------|
| `accounts` | Custom user with 4 roles, profiles, auth, Firebase UID bridge |
| `transports` | Bus / Train / Plane / Ship + routes + schedules |
| `bookings` | Seat selection, booking lifecycle |
| `payments` | Wallet, transactions, simulated payments |
| `qr_system` | QR generation + scan verification |
| `tracking` | Live GPS via Firebase Realtime DB |
| `notifications` | Email + FCM push |
| `dashboard` | Role-based dashboards with charts |
| `reports` | PDF + Excel exports |

---

## Roadmap

- [ ] Real payment gateway integration (Stripe / SSLCommerz)
- [ ] Mobile app (React Native / Flutter) consuming same APIs
- [ ] Multi-language (Bangla / English)
- [ ] Driver mobile companion with live location push
- [ ] Booking refunds + cancellation policy engine
- [ ] Production deploy guide (Docker + Postgres + Redis)

---

## Contributing

PRs welcome. Open an issue first for anything non-trivial.

```bash
git checkout -b feat/your-feature
# commit + push
# open PR
```

---

## License

MIT — free to use, modify, and ship.

---

<div align="center">

Made with care by <a href="https://github.com/Sheikh-SaDiii"><b>MD Sheikh Sadi</b></a>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24&height=100&section=footer" />

</div>
