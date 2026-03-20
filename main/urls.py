"""urls for the main app."""

from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("solar_orbiter", views.SolarOrbiterView.as_view(), name="solar_orbiter"),
    path("data/passes/<str:spacecraft>", views.PassView.as_view(), name="pass_data"),
    path(
        "data/<str:measurement>/<str:spacecraft>", views.DataView.as_view(), name="data"
    ),
    path(
        "trajectory_data/<str:unit>/<str:datatype>",
        views.TrajectoryDataView.as_view(),
        name="trajectory_data",
    ),
    path(
        "l1_data/<str:datatype>",
        views.L1DataView.as_view(),
        name="l1_data",
    ),
]
