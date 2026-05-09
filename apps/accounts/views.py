import json

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .firebase import create_custom_token, upsert_firebase_user, verify_id_token
from .forms import LoginForm, RegisterForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name or user.username}!")
        return redirect(request.GET.get("next") or "dashboard:home")
    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if user.is_provider and not user.is_approved:
            messages.success(
                request,
                "Account created successfully! Your provider account is awaiting admin approval. "
                "Please log in to check your status.",
            )
        else:
            messages.success(
                request,
                f"Account created successfully! Welcome, {user.first_name or user.username}. Please log in.",
            )
        return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("home")


@require_POST
def firebase_login_view(request):
    """Verify a Firebase ID token from the client and log the user into Django.

    Body: JSON {"id_token": "<token>"}.
    Links by firebase_uid first, then by email; creates a User if neither matches.
    """
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    id_token = payload.get("id_token")
    if not id_token:
        return JsonResponse({"ok": False, "error": "missing_id_token"}, status=400)

    try:
        claims = verify_id_token(id_token)
    except Exception as e:
        return JsonResponse({"ok": False, "error": "invalid_token", "detail": str(e)}, status=401)

    uid = claims["uid"]
    email = (claims.get("email") or "").lower()
    name = claims.get("name") or ""

    User = get_user_model()
    user = User.objects.filter(firebase_uid=uid).first()
    if user is None and email:
        user = User.objects.filter(email__iexact=email).first()
        if user:
            user.firebase_uid = uid
            user.save(update_fields=["firebase_uid"])

    if user is None:
        username = email.split("@")[0] if email else f"fb_{uid[:10]}"
        base = username
        i = 1
        while User.objects.filter(username=username).exists():
            i += 1
            username = f"{base}{i}"
        first, _, last = name.partition(" ")
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first,
            last_name=last,
        )
        user.set_unusable_password()
        user.firebase_uid = uid
        user.save()

    login(request, user)
    return JsonResponse({"ok": True, "redirect": str(request.GET.get("next") or "/dashboard/")})


@login_required
def firebase_token_view(request):
    """Mint a Firebase custom token for the currently logged-in Django user.

    The client uses this with `signInWithCustomToken` so the same identity is
    authenticated in both Django (session) and Firebase (so Firestore rules
    can use `request.auth.uid`). The Firebase uid mirrors the Django pk.
    """
    user = request.user
    uid = str(user.pk)
    if user.firebase_uid != uid:
        user.firebase_uid = uid
        user.save(update_fields=["firebase_uid"])

    display_name = (user.get_full_name() or user.username).strip()
    upsert_firebase_user(
        uid,
        email=user.email or "",
        display_name=display_name,
        phone=user.phone or "",
        role=user.role,
    )

    claims = {
        "django_username": user.username,
        "role": user.role,
    }
    token = create_custom_token(uid, claims)
    return JsonResponse({"ok": True, "token": token, "uid": uid})


@login_required
def profile_view(request):
    if request.method == "POST":
        u = request.user
        u.first_name = request.POST.get("first_name", u.first_name)
        u.last_name = request.POST.get("last_name", u.last_name)
        u.phone = request.POST.get("phone", u.phone)
        if request.FILES.get("avatar"):
            u.avatar = request.FILES["avatar"]
        u.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html")
