"""Views for the main app."""

from pathlib import Path
from typing import Any

import bokeh
import numpy as np
import pandas as pd
from bokeh.embed import components
from django.http import HttpRequest, JsonResponse
from django.views.generic import TemplateView, View

from .plots import create_layout


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
    """View for returning measurement data to AjaxDataSource."""

    def get(
        self,
        request: HttpRequest,
        measurement: str,
        spacecraft: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:  # type: ignore
        """Method to get data."""
        csv_files = {
            "IMAP": Path(__file__).parent / "data" / "test_data1.csv",
            "SO": Path(__file__).parent / "data" / "test_data2.csv",
        }
        df = pd.read_csv(csv_files[spacecraft], parse_dates=True)
        # Nan values are not JSON serializable
        df = df.replace({np.nan: None})
        # Format datetime as Unix epoch time
        df = df.rename(columns={df.columns[0]: "date"})
        df["date"] = pd.to_datetime(df["date"], utc=True).astype("int64") // 10**6

        # Create JSON response
        dates = df["date"].tolist()
        measurements = df[measurement].tolist()
        data = {"measurement": measurements, "date": dates}
        return JsonResponse(data)
