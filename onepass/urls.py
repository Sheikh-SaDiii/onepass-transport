from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.transports.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("transports/", include("apps.transports.urls", namespace="transports")),
    path("bookings/", include("apps.bookings.urls", namespace="bookings")),
    path("payments/", include("apps.payments.urls", namespace="payments")),
    path("qr/", include("apps.qr_system.urls", namespace="qr")),
    path("tracking/", include("apps.tracking.urls", namespace="tracking")),
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
