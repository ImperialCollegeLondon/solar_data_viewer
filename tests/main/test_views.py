"""Test suite for the main views."""

from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch

from django.http import JsonResponse
from django.urls import reverse

from .view_utils import TemplateOkMixin


class TestIndexView(TemplateOkMixin):
    """Test suite for the Index view."""

    _template_name = "main/index.html"

    def _get_url(self):
        return reverse("main:index")

    def test_get(self, client):
        """Tests the get method and the data provided."""
        import bokeh

        endpoint = reverse("main:index")
        response = client.get(endpoint)
        assert response.status_code == HTTPStatus.OK
        assert "<script" in response.context["script"]
        assert "<div" in response.context["div"]
        assert response.context["bokeh_version"] == bokeh.__version__


class TestDataView:
    """Test suite for the Data view."""

    def test_get(self, client):
        """Test the get method."""
        with patch("main.views.process_data_from_test_csvs") as process_data_mock:
            process_data_mock.return_value = {
                "measurement": [3.0, 4.0, 5.0],
                "date": [1767867720000, 1767867780000, 1767867840000],
            }
            measurement, spacecraft = "speed", "IMAP"
            endpoint = reverse("main:data", args=[measurement, spacecraft])
            response = client.get(endpoint)
            assert isinstance(response, JsonResponse)
            process_data_mock.assert_called_with(spacecraft, measurement, "3d")


class TestSolarOrbiterView(TemplateOkMixin):
    """Test suite for the Solar Orbiter view."""

    _template_name = "main/solar_orbiter.html"

    def _get_url(self):
        return reverse("main:solar_orbiter")

    def test_get(self, client):
        """Tests the get method and the data provided."""
        import bokeh

        endpoint = reverse("main:solar_orbiter")
        response = client.get(endpoint)
        assert response.status_code == HTTPStatus.OK
        assert "<script" in response.context["script"]
        assert "<div" in response.context["div"]
        assert response.context["bokeh_version"] == bokeh.__version__


class TestTrajectoryDataView:
    """Test suite for the Trajectory Data view."""

    def test_get(self, client):
        """Test the get method."""
        with patch("main.views.datetime") as datetime_mock:
            time = datetime.now()
            datetime_mock.now.return_value = time

            with patch("main.views.static_solar_orbiter_data") as static_data_mock:
                static_data_mock.return_value = {
                    "name": ["Sun", "Solar Orbiter", "Earth"],
                    "x": [0.0, 1.1, 2.2],
                    "y": [0.0, 3.3, 4.4],
                    "colour": ["orange", "blue", "green"],
                }
                unit, datatype = "AU", "static"
                endpoint = reverse("main:trajectory_data", args=[unit, datatype])
                response = client.get(endpoint)
                assert isinstance(response, JsonResponse)
                static_data_mock.assert_called_with(time, unit)

            with patch("main.views.trajectory_solar_orbiter_data") as traj_data_mock:
                times = [time + timedelta(days=i) for i in range(8)]
                traj_data_mock.return_value = {
                    "x": [0.0, 1.1, 2.2],
                    "y": [0.0, 3.3, 4.4],
                }
                unit, datatype = "angle", "trajectory"
                endpoint = reverse("main:trajectory_data", args=[unit, datatype])
                response = client.get(endpoint)
                assert isinstance(response, JsonResponse)
                traj_data_mock.assert_called_with(times, unit)
