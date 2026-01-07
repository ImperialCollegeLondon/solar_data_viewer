"""Views for the main app."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Example view function making use of a template."""
    return render(request, "main/index.html")
