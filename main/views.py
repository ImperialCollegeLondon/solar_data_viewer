"""Views for the main app."""

from datetime import datetime
from typing import Any, Literal

import bokeh
from bokeh.embed import components
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.views.generic import TemplateView, View

from .cache import set_l1_trajectory_cache, set_so_trajectory_cache
from .plots import create_l1_plot, create_solar_orbiter_layout, create_timeseries_layout
from .trajectory import check_if_so_in_communication, generate_solar_orbiter_statistics
from .utils import process_data_from_test_csvs, process_pass_data_from_test_csvs


class IndexView(TemplateView):
    """View to display the index page."""

    template_name = "main/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore
        """Add HTML components and Bokeh version to the context."""
        context = super().get_context_data(**kwargs)
        # Get timeseries components
        layout = create_timeseries_layout()
        ts_script, ts_div = components(layout)

        # Get trajectory plot components
        l1_plot = create_l1_plot()
        l1_script, l1_div = components(l1_plot)

        # Get time the plot was generated
        cache_data = cache.get(
            f"l1_trajectory_data-{datetime.today().strftime('%Y%m%d')}"
        )
        time = cache_data["time"].strftime("%Y-%m-%d %H:%M:%S") if cache_data else None
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
        # Get trajectory plot components
        layout = create_solar_orbiter_layout()
        script, div = components(layout)

        # Get time the plot was generated
        cache_data = cache.get(f"trajectory_data-{datetime.today().strftime('%Y%m%d')}")
        time = cache_data["time"].strftime("%Y-%m-%d %H:%M:%S") if cache_data else None
        context.update({"script": script, "div": div, "time": time})

        # Get solar orbiter statistics
        stats = generate_solar_orbiter_statistics()
        context.update(stats)
        context["bokeh_version"] = bokeh.__version__
        context["message"] = check_if_so_in_communication()
        return context


class TrajectoryDataView(View):
    """View for returning trajectory data to the AjaxDataSource."""

    def get(  # type: ignore
        self,
        request: HttpRequest,
        unit: Literal["AU", "angle"],
        datatype: Literal["static", "trajectory", "arrow"],
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Method to handle GET requests for SO trajectory data.

        Args:
            request: The incoming HTTP request.
            unit: The units on the plot, either AU (astronomical units) or angle
                (Earth separation angles).
            datatype: Whether to retrieve static, trajectory or arrow data.
            *args: Additional positional arguments.
            **kwargs: Additional key word arguments.

        Returns:
            A JSON response containing the trajectory data for Solar Orbiter.
        """
        date = datetime.today()
        cache_key = f"trajectory_data-{date.strftime('%Y%m%d')}"
        data = cache.get(cache_key)
        if data is None:
            set_so_trajectory_cache()
            data = cache.get(cache_key)

        return JsonResponse(data[datatype][unit])


class L1DataView(View):
    """View for returning L1 trajectory data to the AjaxDataSource."""

    def get(  # type: ignore
        self,
        request: HttpRequest,
        datatype: Literal["static", "trajectory", "arrow"],
        spacecraft: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Method to handle GET requests for L1 trajectory data.

        Args:
            request: The incoming HTTP request.
            datatype: Whether to retrieve static, trajectory or arrow data.
            spacecraft: Name of spacecraft to get arrow coordinates for.
            *args: Additional positional arguments.
            **kwargs: Additional key word arguments.

        Returns:
            A JSON response containing the trajectory data for L1 spacecraft.
        """
        date = datetime.today()
        cache_key = f"l1_trajectory_data-{date.strftime('%Y%m%d')}"
        data = cache.get(cache_key)
        if data is None:
            set_l1_trajectory_cache()
            data = cache.get(cache_key)
        if datatype == "arrow":
            if spacecraft:
                return JsonResponse(data[datatype][spacecraft])
            else:
                raise ValueError(
                    "No spacecraft provided to retrieve arrow coordinates for."
                )

        return JsonResponse(data[datatype])


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
        data = process_pass_data_from_test_csvs(spacecraft)

        return JsonResponse(data)
