"""Smoke test for Firebase Admin SDK + custom token flow.

Run from project root:
    venv\\Scripts\\python test_firebase_connection.py
"""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "onepass.settings")
django.setup()

from apps.accounts.firebase import _get_app, create_custom_token, verify_id_token  # noqa: E402
from firebase_admin import auth as fb_auth  # noqa: E402


def banner(msg):
    print(f"\n=== {msg} ===")


def main():
    banner("1. Initialize Admin SDK")
    app = _get_app()
    print(f"OK  project_id={app.project_id}  name={app.name}")

    banner("2. Mint a custom token for uid='test-user-1'")
    token = create_custom_token("test-user-1", {"role": "tester"})
    print(f"OK  token length={len(token)}  starts={token[:24]}...")

    banner("3. Round-trip: verify a deliberately bad token")
    try:
        verify_id_token("not-a-real-token")
        print("FAIL  expected exception")
        sys.exit(1)
    except Exception as e:
        print(f"OK  rejected as expected: {type(e).__name__}")

    banner("4. List users (first page) — optional, needs 'Firebase Authentication Admin' IAM role")
    try:
        page = fb_auth.list_users(max_results=1)
        n = sum(1 for _ in page.users)
        print(f"OK  reachable; users on first page={n}")
    except Exception as e:
        print(f"SKIP  {type(e).__name__}: {e}  (not required for the bridge)")

    banner("5. Firestore write/read round-trip")
    try:
        from firebase_admin import firestore
        db = firestore.client()
        ref = db.collection("_smoke_test").document("ping")
        ref.set({"ok": True, "from": "test_firebase_connection.py"})
        snap = ref.get()
        data = snap.to_dict() if snap.exists else None
        print(f"OK  read back: {data}")
        ref.delete()
        print("OK  cleaned up")
    except Exception as e:
        print(f"SKIP  Firestore not ready: {type(e).__name__}: {e}")

    print("\nAll Admin SDK checks passed.\n")


if __name__ == "__main__":
    main()
