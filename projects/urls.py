from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path(
        "ref/<str:reference_number>/",
        views.ProjectDetailView.as_view(),
        name="detail_by_ref",
    ),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="detail"),
    path("add/", views.ProjectCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="delete"),
]
