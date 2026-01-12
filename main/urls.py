"""urls for the main app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("plots", views.PlotsView.as_view()),
]
