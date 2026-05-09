"""Firebase Admin SDK initialization. Safe no-op if creds are missing."""
import os
from pathlib import Path
from django.conf import settings

_app = None
_enabled = False


def init():
    global _app, _enabled
    if _app is not None:
        return _app
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        return None

    sa_path = Path(settings.BASE_DIR) / settings.FIREBASE["SERVICE_ACCOUNT"]
    if not sa_path.exists():
        return None
    try:
        cred = credentials.Certificate(str(sa_path))
        opts = {}
        if settings.FIREBASE["DATABASE_URL"]:
            opts["databaseURL"] = settings.FIREBASE["DATABASE_URL"]
        if settings.FIREBASE["STORAGE_BUCKET"]:
            opts["storageBucket"] = settings.FIREBASE["STORAGE_BUCKET"]
        _app = firebase_admin.initialize_app(cred, opts or None)
        _enabled = True
        return _app
    except Exception:
        return None


def is_enabled() -> bool:
    return _enabled


def push_gps(transport_id: str, lat: float, lng: float, status: str = "running"):
    """Push a GPS ping to Realtime DB. No-op if Firebase not configured."""
    if not init():
        return False
    from firebase_admin import db
    ref = db.reference(f"gps_tracking/{transport_id}")
    ref.set({"lat": lat, "lng": lng, "status": status})
    return True
