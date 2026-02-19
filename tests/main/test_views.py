"""Test suite for the main views."""

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
        mock_data = {
            "static": {
                "AU": {
                    "x": [0.0, 1.1, 2.2],
                    "y": [0.0, 3.3, 4.4],
                },
                "angle": {
                    "x": [5.5, 6.6, 7.7],
                    "y": [8.8, 9.9, 10.10],
                },
            },
            "trajectory": {
                "AU": {
                    "x": [5, 6],
                    "y": [7, 8],
                },
                "angle": {
                    "x": [4, 3],
                    "y": [2, 1],
                },
            },
        }

        with patch("main.views.cache") as cache_mock:
            cache_mock.get.return_value = mock_data
            for unit in ["AU", "angle"]:
                for datatype in ["trajectory", "static"]:
                    endpoint = reverse("main:trajectory_data", args=[unit, datatype])
                    response = client.get(endpoint)
                    cache_mock.get.assert_called_with("trajectory_data")
                    assert isinstance(response, JsonResponse)
                    assert response.json() == mock_data[datatype][unit]

        with patch("main.views.cache") as empty_cache_mock:
            with patch("main.views.set_trajectory_cache") as cache_setter_mock:
                empty_cache_mock.get.side_effect = [None, mock_data]
                endpoint = reverse("main:trajectory_data", args=["AU", "static"])
                response = client.get(endpoint)
                cache_setter_mock.assert_called_once()
