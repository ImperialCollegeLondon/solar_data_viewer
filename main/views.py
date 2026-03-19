"""Views for the main app."""

from typing import Any, Literal

import bokeh
from bokeh.embed import components
from django.http import HttpRequest, JsonResponse
from django.views.generic import TemplateView, View

from .models import TrajectoryCache
from .plots import create_l1_plot, create_solar_orbiter_layout, create_timeseries_layout
from .tasks import set_l1_trajectory_cache, set_so_trajectory_cache
from .trajectory import (
    generate_solar_orbiter_statistics,
)
from .utils import process_data_from_test_csvs


class IndexView(TemplateView):
    """View to display the index page."""

    template_name = "main/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore
        """Add HTML components and Bokeh version to the context."""
        context = super().get_context_data(**kwargs)
        layout = create_timeseries_layout()
        ts_script, ts_div = components(layout)
        l1_plot = create_l1_plot()
        l1_script, l1_div = components(l1_plot)

        # Get time from cache
        if TrajectoryCache.objects.filter(plot="L1").exists():
            time = TrajectoryCache.objects.get(plot="L1").time_generated
        else:
            time = None

        context.update(
            {
                "ts_script": ts_script,
                "ts_div": ts_div,
                "l1_script": l1_script,
                "l1_div": l1_div,
                "time": time,
            }
        )
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


class SolarOrbiterView(TemplateView):
    """View to display the Solar Orbiter data."""

    template_name = "main/solar_orbiter.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore
        """Add HTML components and Bokeh version to the context."""
        context = super().get_context_data(**kwargs)
        layout = create_solar_orbiter_layout()
        script, div = components(layout)

        # Get time from cache
        if TrajectoryCache.objects.filter(plot="SO").exists():
            time = TrajectoryCache.objects.get(plot="SO").time_generated
        else:
            time = None
        context.update({"script": script, "div": div, "time": time})

        stats = generate_solar_orbiter_statistics()
        context.update(stats)
        context["bokeh_version"] = bokeh.__version__
        return context


class TrajectoryDataView(View):
    """View for returning trajectory data to the AjaxDataSource."""

    def get(  # type: ignore
        self,
        request: HttpRequest,
        unit: Literal["AU", "angle"],
        datatype: Literal["static", "trajectory"],
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Method to handle GET requests for SO trajectory data.

        Args:
            request: The incoming HTTP request.
            unit: The units on the plot, either AU (astronomical units) or angle
                (Earth separation angles).
            datatype: Whether to retrieve static or trajectory data.
            *args: Additional positional arguments.
            **kwargs: Additional key word arguments.

        Returns:
            A JSON response containing the trajectory data for Solar Orbiter.
        """
        if TrajectoryCache.objects.filter(plot="SO").exists():
            data = TrajectoryCache.objects.get(plot="SO").data

        else:
            set_so_trajectory_cache()
            data = TrajectoryCache.objects.get(plot="SO").data

        return JsonResponse(data[datatype][unit])


class L1DataView(View):
    """View for returning L1 trajectory data to the AjaxDataSource."""

    def get(  # type: ignore
        self,
        request: HttpRequest,
        datatype: Literal["static", "trajectory"],
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Method to handle GET requests for L1 trajectory data.

        Args:
            request: The incoming HTTP request.
            datatype: Whether to retrieve static or trajectory data.
            *args: Additional positional arguments.
            **kwargs: Additional key word arguments.

        Returns:
            A JSON response containing the trajectory data for L1 spacecraft.
        """
        if TrajectoryCache.objects.filter(plot="L1").exists():
            data = TrajectoryCache.objects.get(plot="L1").data

        else:
            set_l1_trajectory_cache()
            data = TrajectoryCache.objects.get(plot="L1").data

        return JsonResponse(data[datatype])
