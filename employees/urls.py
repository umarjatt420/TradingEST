from django.urls import path

from . import views

app_name = "employees"

urlpatterns = [
    path("", views.EmployeeListView.as_view(), name="list"),
    path("<int:pk>/", views.EmployeeDetailView.as_view(), name="detail"),
    path("add/", views.EmployeeCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.EmployeeUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.EmployeeDeleteView.as_view(), name="delete"),
]
