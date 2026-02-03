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
