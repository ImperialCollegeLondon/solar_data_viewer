"""Test suite for the main views."""

from http import HTTPStatus

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
