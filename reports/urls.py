from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("accounts-summary/", views.AccountsSummaryView.as_view(), name="accounts_summary"),
    path("tax/", views.TaxReportView.as_view(), name="tax_report"),
    path("monthly/", views.MonthlyReportView.as_view(), name="monthly_report"),
]
