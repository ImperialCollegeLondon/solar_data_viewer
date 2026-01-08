"""Views for the main app."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Placeholder view function."""
    return render(request, "main/index.html")
