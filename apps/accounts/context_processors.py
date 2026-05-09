def user_role(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"role": None}
    return {
        "role": user.role,
        "is_admin_role": user.is_admin_role,
        "is_provider": user.is_provider,
        "is_user_role": user.is_user,
        "is_pending_approval": user.is_pending_approval,
    }
