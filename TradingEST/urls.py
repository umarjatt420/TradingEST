from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/favicon.ico", permanent=True),
    ),
    path("", RedirectView.as_view(pattern_name="reports:dashboard", permanent=False)),
    path("accounts/", include("accounts.urls")),
    path("transactions/", include("transactions.urls")),
    path("projects/", include("projects.urls")),
    path("employees/", include("employees.urls")),
    path("reports/", include("reports.urls")),
]
