# OnePass — Unified Multi-Transport Ticket Booking System

Django + Firebase platform for booking buses, trains, planes, and ships from one interface.
Four roles: Admin, Service Provider, Service Driver, User.

## Quick Start

```bash
# 1. create + activate virtualenv
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate      # macOS/Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# edit .env and fill in your secrets

# 4. database
python manage.py migrate
python manage.py seed_demo      # creates demo users, providers, transports

# 5. run
python manage.py runserver
```

Open http://127.0.0.1:8000

## Demo Accounts (after `seed_demo`)

| Role     | Email                    | Password    |
|----------|--------------------------|-------------|
| Admin    | admin@onepass.local      | admin12345  |
| Provider | provider@onepass.local   | provider123 |
| Driver   | driver@onepass.local     | driver123   |
| User     | user@onepass.local       | user12345   |

## Firebase Setup

1. Create a project at https://console.firebase.google.com
2. Enable: Authentication (Email/Password), Firestore, Realtime Database, Storage, Cloud Messaging
3. Project Settings → Service accounts → **Generate new private key** → save as `serviceAccountKey.json` in project root
4. Project Settings → General → copy web config values into `.env`

The app runs without Firebase configured (uses local SQLite + dummy QR/tracking). Real-time
seat updates and GPS tracking activate once Firebase credentials are present.

## Apps

| App           | Purpose                                              |
|---------------|------------------------------------------------------|
| accounts      | Custom user with 4 roles, profiles, auth             |
| transports    | Bus / Train / Plane / Ship + routes + schedules      |
| bookings      | Seat selection, booking lifecycle                    |
| payments      | Wallet, transactions, simulated payments             |
| qr_system     | QR generation + scan verification                    |
| tracking      | Live GPS via Firebase Realtime DB                    |
| notifications | Email + FCM push                                     |
| dashboard     | Role-based dashboards with charts                    |
| reports       | PDF + Excel exports                                  |

## Tech

Django 5 · Bootstrap 5 · Chart.js · Firebase Admin SDK · qrcode · ReportLab · openpyxl
