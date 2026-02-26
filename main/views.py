"""Views for the main app."""

from typing import Any

import bokeh
from bokeh.embed import components
from django.http import HttpRequest, JsonResponse
from django.views.generic import TemplateView, View

from .plots import create_layout
from .utils import process_data_from_test_csvs, process_pass_data_from_test_csvs


class IndexView(TemplateView):
    """View to display the index page."""

    template_name = "main/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore
        """Add HTML components and Bokeh version to the context."""
        context = super().get_context_data(**kwargs)
        layout = create_layout()
        script, div = components(layout)
        context.update({"script": script, "div": div})
        context["bokeh_version"] = bokeh.__version__
        return context


class DataView(View):
    """View for returning measurement data to the AjaxDataSource."""

    def get(  # type: ignore
        self,
        request: HttpRequest,
        measurement: str,
        spacecraft: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Method to handle GET requests for spacecraft data.

        Args:
            request: The incoming HTTP request.
            measurement: Name of the measurement to get data for.
            spacecraft: Name of the spacecraft to retrieve data for.
            *args: Additional positional arguments.
            **kwargs: Additional key word arguments.

        Returns:
            A JSON response containing the dates and values for the specific
                spacecraft and measurement type.
        """
        range_param = request.GET.get("range", "3d")
        data = process_data_from_test_csvs(spacecraft, measurement, range_param)
        return JsonResponse(data)


class PassView(View):
    """View for returning pass data to the AjaxDataSource."""

    def get(  # type: ignore
        self,
        request: HttpRequest,
        spacecraft: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Method to handle GET requests for spacecraft pass data.

        Args:
            request: The incoming HTTP request.
            spacecraft: Name of the spacecraft to retrieve pass data for.
            *args: Additional positional arguments.
            **kwargs: Additional key word arguments.

        Returns:
            A JSON response containing the start and end times for the specific
            spacecraft passes in milliseconds.
        """
        range_param = request.GET.get("range", "3d")

        data = process_pass_data_from_test_csvs(spacecraft, range_param)

        return JsonResponse(data)
