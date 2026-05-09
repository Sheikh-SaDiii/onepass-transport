from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    def deco(view):
        @wraps(view)
        def _wrapped(request, *a, **kw):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            if request.user.is_superuser:
                return view(request, *a, **kw)
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access that page.")
                return redirect("dashboard:home")
            # Block unapproved providers from provider tools
            if request.user.is_provider and not request.user.is_approved:
                messages.warning(request, "Your provider account is awaiting admin approval.")
                return redirect("dashboard:home")
            return view(request, *a, **kw)
        return _wrapped
    return deco
