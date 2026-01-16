"""urls for the main app."""

from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("plots", views.PlotsView.as_view(), name="plots"),
]
