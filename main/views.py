"""Views for the main app."""

from typing import Any

import bokeh
from bokeh.embed import components
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from .plots import create_plots


def index(request: HttpRequest) -> HttpResponse:
    """Placeholder view function."""
    return render(request, "main/index.html")


class PlotsView(TemplateView):
    """View to display the ACE data plots."""

    template_name = "main/plots.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore
        """Add HTML components and Bokeh version to the context."""
        context = super().get_context_data(**kwargs)
        layout = create_plots()
        script, div = components(layout)
        context.update({"script": script, "div": div})
        context["bokeh_version"] = bokeh.__version__
        return context
