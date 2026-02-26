"""urls for the main app."""

from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    # 1. SPECIFIC ROUTE GOES FIRST
    # Django will check if the URL explicitly says "passes" before moving on
    path("data/passes/<str:spacecraft>", views.PassView.as_view(), name="pass_data"),
    # 2. CATCH-ALL ROUTE GOES SECOND
    # If the URL is "data/speed/IMAP", it will skip the above and match this one
    path(
        "data/<str:measurement>/<str:spacecraft>", views.DataView.as_view(), name="data"
    ),
]
