from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from apps.accounts.decorators import role_required
from apps.accounts.models import User, Role, ProviderProfile
from apps.notifications.models import Notification


@login_required
@role_required("admin")
def users_list(request):
    role = request.GET.get("role", "")
    q = request.GET.get("q", "").strip()
    qs = User.objects.all().order_by("-date_joined")
    if role:
        qs = qs.filter(role=role)
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q))
    return render(
        request,
        "dashboard/admin_users.html",
        {"users": qs[:100], "role_filter": role, "q": q, "roles": Role.choices},
    )


@login_required
@role_required("admin")
def user_suspend(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot suspend a superuser.")
        return redirect("dashboard:admin_users")
    user.is_active = not user.is_active
    user.save()
    state = "reactivated" if user.is_active else "suspended"
    messages.success(request, f"User {user.username} {state}.")
    return redirect("dashboard:admin_users")


@login_required
@role_required("admin")
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot delete a superuser.")
        return redirect("dashboard:admin_users")
    name = user.username
    user.delete()
    messages.success(request, f"User {name} deleted.")
    return redirect("dashboard:admin_users")


@login_required
@role_required("admin")
def providers_pending(request):
    pending = User.objects.filter(role=Role.PROVIDER, is_approved=False).select_related("provider_profile")
    approved = User.objects.filter(role=Role.PROVIDER, is_approved=True).select_related("provider_profile")[:30]
    return render(
        request,
        "dashboard/admin_providers.html",
        {"pending": pending, "approved": approved},
    )


@login_required
@role_required("admin")
def provider_approve(request, user_id):
    user = get_object_or_404(User, pk=user_id, role=Role.PROVIDER)
    user.is_approved = True
    user.save()
    Notification.objects.create(
        user=user,
        title="Account approved",
        body="Your provider account has been approved. You can now publish schedules.",
        kind="info",
    )
    messages.success(request, f"Approved {user.username}.")
    return redirect("dashboard:admin_providers")


@login_required
@role_required("admin")
def provider_reject(request, user_id):
    user = get_object_or_404(User, pk=user_id, role=Role.PROVIDER)
    user.is_approved = False
    user.is_active = False
    user.save()
    Notification.objects.create(
        user=user,
        title="Account rejected",
        body="Your provider application was rejected. Please contact support.",
        kind="alert",
    )
    messages.success(request, f"Rejected {user.username}.")
    return redirect("dashboard:admin_providers")
