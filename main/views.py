"""Views for the main app."""

from pathlib import Path
from typing import Any

import bokeh
from bokeh.embed import components
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from .plots import create_layout


def index(request: HttpRequest) -> HttpResponse:
    """Placeholder view function."""
    return render(request, "main/index.html")


class PlotsView(TemplateView):
    """View to display the plots."""

    template_name = "main/plots.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore
        """Add HTML components and Bokeh version to the context."""
        context = super().get_context_data(**kwargs)
        csv_files = (
            Path(__file__).parent / "data" / "test_data1.csv",
            Path(__file__).parent / "data" / "test_data2.csv",
        )
        names = ["Spacecraft 1", "Spacecraft 2"]
        layout = create_layout(csv_files, names, default_index=0)
        script, div = components(layout)
        context.update({"script": script, "div": div})
        context["bokeh_version"] = bokeh.__version__
        return context
