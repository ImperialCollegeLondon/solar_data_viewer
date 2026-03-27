"""Test suite for the main views."""

from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch

import pytest
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
        assert "<script" in response.context["ts_script"]
        assert "<div" in response.context["ts_div"]
        assert "<script" in response.context["l1_script"]
        assert "<div" in response.context["l1_div"]
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

    @patch("main.views.generate_solar_orbiter_statistics")
    def test_get(self, stats_mock, client):
        """Tests the get method and the data provided."""
        import bokeh

        # Check SO stats are added
        mocked_stats = {
            "sun_earth_angle": 10,
            "visibility": "GOOD",
            "dist_upstream_earth": 5,
            "CME400time": 11,
            "CME1000time": 14,
            "sun_spacecraft_distance": 300,
            "lat_relative_to_earth": 2,
            "lat_direction": "N",
        }
        stats_mock.return_value = mocked_stats

        endpoint = reverse("main:solar_orbiter")
        response = client.get(endpoint)
        assert response.status_code == HTTPStatus.OK
        assert "<script" in response.context["script"]
        assert "<div" in response.context["div"]
        assert response.context["bokeh_version"] == bokeh.__version__

        stats_mock.assert_called_once()
        assert all(mocked_stats[k] == response.context[k] for k in mocked_stats.keys())


class TestTrajectoryDataView:
    """Test suite for the Trajectory Data view."""

    def test_get(self, client):
        """Test the get method."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        mock_data = {
            "static": {
                "AU": {"static": "AU"},
                "angle": {"static": "angle"},
            },
            "trajectory": {
                "AU": {"trajectory": "AU"},
                "angle": {"trajectory": "angle"},
            },
            "arrow": {
                "AU": {
                    "x_start": [0],
                    "x_end": [1],
                    "y_start": [0],
                    "y_end": [1],
                },
                "angle": {
                    "x_start": [0],
                    "x_end": [1],
                    "y_start": [0],
                    "y_end": [1],
                },
            },
        }

        with patch("main.views.cache") as cache_mock:
            # Data already in cache
            cache_mock.get.side_effect = [mock_data, today] * 6
            for unit in ["AU", "angle"]:
                for datatype in ["trajectory", "static", "arrow"]:
                    endpoint = reverse("main:trajectory_data", args=[unit, datatype])
                    response = client.get(endpoint)
                    cache_mock.get.assert_any_call("trajectory_data")
                    cache_mock.get.assert_any_call("time_generated_so")
                    assert isinstance(response, JsonResponse)
                    assert response.json() == mock_data[datatype][unit]

            # Data in cache but from yesterday
            with patch("main.views.set_so_trajectory_cache") as cache_setter_mock:
                cache_mock.get.side_effect = [mock_data, yesterday, mock_data]
                endpoint = reverse("main:trajectory_data", args=["AU", "static"])
                response = client.get(endpoint)
                cache_setter_mock.assert_called_once()
                assert response.json() == mock_data["static"]["AU"]

            # Empty cache
            with patch("main.views.set_so_trajectory_cache") as cache_setter_mock:
                cache_mock.get.side_effect = [None, None, mock_data]
                endpoint = reverse("main:trajectory_data", args=["AU", "trajectory"])
                response = client.get(endpoint)
                cache_setter_mock.assert_called_once()
                assert response.json() == mock_data["trajectory"]["AU"]


class TestL1DataView:
    """Test suite for the L1 Data View."""

    def test_get(self, client):
        """Test the get method."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        mock_data = {
            "static": {"static": "data"},
            "trajectory": {"trajectory": "data"},
        }

        with patch("main.views.cache") as cache_mock:
            # Data already in cache
            cache_mock.get.side_effect = [mock_data, today] * 2
            for datatype in ["trajectory", "static"]:
                endpoint = reverse("main:l1_data", args=[datatype])
                response = client.get(endpoint)
                cache_mock.get.assert_any_call("l1_trajectory_data")
                cache_mock.get.assert_any_call("time_generated_l1")
                assert isinstance(response, JsonResponse)
                assert response.json() == mock_data[datatype]

            # Data in cache but from yesterday
            with patch("main.views.set_l1_trajectory_cache") as cache_setter_mock:
                cache_mock.get.side_effect = [mock_data, yesterday, mock_data]
                endpoint = reverse("main:l1_data", args=["static"])
                response = client.get(endpoint)
                cache_setter_mock.assert_called_once()
                assert response.json() == mock_data["static"]

            # Empty cache
            with patch("main.views.set_l1_trajectory_cache") as cache_setter_mock:
                cache_mock.get.side_effect = [None, None, mock_data]
                endpoint = reverse("main:l1_data", args=["trajectory"])
                response = client.get(endpoint)
                cache_setter_mock.assert_called_once()
                assert response.json() == mock_data["trajectory"]

    def test_get_arrow(self, client):
        """Test the get method to get arrow data."""
        mock_data = {"arrow": {"spacecraft": {"data": "data"}}}

        with patch("main.views.cache") as cache_mock:
            cache_mock.get.side_effect = [mock_data, datetime.now()]
            # No spacecraft provided
            with pytest.raises(
                ValueError,
            ):
                endpoint = reverse("main:l1_data", args=["arrow"])
                response = client.get(endpoint)

        with patch("main.views.cache") as cache_mock:
            cache_mock.get.side_effect = [mock_data, datetime.now()]
            # With spacecraft
            endpoint = reverse("main:l1_arrow_data", args=["arrow", "spacecraft"])
            response = client.get(endpoint)
            assert isinstance(response, JsonResponse)
            assert response.json() == {"data": "data"}
