from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import DashboardView, logout_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/logout/", logout_view, name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", DashboardView.as_view(), name="dashboard"),
    path("medicamentos/", include(("parametricas.urls", "parametricas"), namespace="parametricas")),
    path("afiliados/", include(("radicacion.urls", "radicacion"), namespace="radicacion")),
    path("formula/", include(("radicacion.urls_formulas", "formula"), namespace="formula")),
    path("select2/", include("django_select2.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
