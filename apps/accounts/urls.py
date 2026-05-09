from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("firebase-login/", views.firebase_login_view, name="firebase_login"),
    path("firebase-token/", views.firebase_token_view, name="firebase_token"),
]
