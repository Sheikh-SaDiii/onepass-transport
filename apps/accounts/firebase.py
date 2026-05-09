from pathlib import Path

import firebase_admin
from django.conf import settings
from firebase_admin import auth as fb_auth
from firebase_admin import credentials

_app = None


def _get_app():
    global _app
    if _app is not None:
        return _app
    if firebase_admin._apps:
        _app = firebase_admin.get_app()
        return _app

    sa_path = settings.FIREBASE.get("SERVICE_ACCOUNT") or "serviceAccountKey.json"
    sa_file = Path(sa_path)
    if not sa_file.is_absolute():
        sa_file = Path(settings.BASE_DIR) / sa_file

    if not sa_file.exists():
        raise RuntimeError(
            f"Firebase service account file not found at {sa_file}. "
            "Download it from Firebase Console > Project Settings > Service accounts "
            "and set FIREBASE_SERVICE_ACCOUNT in your env (relative to BASE_DIR or absolute)."
        )

    cred = credentials.Certificate(str(sa_file))
    _app = firebase_admin.initialize_app(cred)
    return _app


def verify_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return its decoded claims."""
    _get_app()
    return fb_auth.verify_id_token(id_token)


def create_custom_token(uid: str, claims: dict | None = None) -> str:
    """Mint a Firebase custom token for the given uid (decoded from bytes)."""
    _get_app()
    token = fb_auth.create_custom_token(uid, claims or {})
    return token.decode("utf-8") if isinstance(token, bytes) else token


ROLE_LABELS = {"admin": "Admin", "provider": "Service Provider", "user": "User"}


def upsert_firebase_user(
    uid: str,
    *,
    email: str = "",
    display_name: str = "",
    phone: str = "",
    role: str = "",
) -> None:
    """Create or update the Firebase Auth record for `uid`.

    Sets email + display_name (suffixed with role label so the Auth console
    shows it) and stores the role as a Firebase custom claim so Firestore
    rules and clients can read it from the ID token.
    """
    _get_app()
    label = ROLE_LABELS.get(role, "")
    name = f"{display_name} ({label})" if display_name and label else display_name

    fields = {}
    if email:
        fields["email"] = email
    if name:
        fields["display_name"] = name
    if phone and phone.startswith("+") and len(phone) >= 8:
        fields["phone_number"] = phone

    if fields:
        try:
            fb_auth.update_user(uid, **fields)
        except fb_auth.UserNotFoundError:
            fb_auth.create_user(uid=uid, **fields)
        except (fb_auth.EmailAlreadyExistsError, fb_auth.PhoneNumberAlreadyExistsError):
            pass

    if role:
        try:
            fb_auth.set_custom_user_claims(uid, {"role": role})
        except fb_auth.UserNotFoundError:
            pass
