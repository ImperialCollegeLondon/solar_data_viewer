"""urls for the main app."""

from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("data/passes/<str:spacecraft>", views.PassView.as_view(), name="pass_data"),
    path(
        "data/<str:measurement>/<str:spacecraft>", views.DataView.as_view(), name="data"
    ),
]
