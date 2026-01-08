"""Utility module for view tests."""

from http import HTTPStatus

from pytest_django.asserts import assertTemplateUsed


class TemplateOkMixin:
    """Mixin for tests that verify the correct template is used.

    Note: Using this requires the test class to define:
        - A `_get_url` method.
        - A `_template_name` variable.
    """

    def test_template_used(self, admin_client):
        """Test the correct template is used by the GET request."""
        with assertTemplateUsed(template_name=self._template_name):
            response = admin_client.get(self._get_url())
        assert response.status_code == HTTPStatus.OK
