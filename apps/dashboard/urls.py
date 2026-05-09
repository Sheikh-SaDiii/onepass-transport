from django.urls import path
from . import views, admin_views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    # Admin
    path("admin/users/", admin_views.users_list, name="admin_users"),
    path("admin/users/<int:user_id>/suspend/", admin_views.user_suspend, name="admin_user_suspend"),
    path("admin/users/<int:user_id>/delete/", admin_views.user_delete, name="admin_user_delete"),
    path("admin/providers/", admin_views.providers_pending, name="admin_providers"),
    path("admin/providers/<int:user_id>/approve/", admin_views.provider_approve, name="admin_provider_approve"),
    path("admin/providers/<int:user_id>/reject/", admin_views.provider_reject, name="admin_provider_reject"),
]
