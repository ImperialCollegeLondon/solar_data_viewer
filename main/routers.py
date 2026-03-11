"""Routers for the database."""

from django.db import models


class Router:
    """A router to control where models are read from."""

    route_app_labels = "main"

    def _select_db(self, model_name: str):
        """Internal function to select the right database."""
        if model_name.lower().startswith("imap"):
            return "imap"
        if model_name.lower().startswith("so"):
            return "so"
        return None

    def db_for_read(self, model: models.Model, **hints):
        """Select the database to read."""
        return self._select_db(model._meta.model_name)

    def db_for_write(self, model: models.Model, **hints):
        """Select the database to read."""
        return self._select_db(model._meta.model_name)

    def allow_migrate(
        self, db: str, app_label: str, model_name: str | None = None, **hints
    ):
        """Make sure the models appear in the right db during migrations."""
        return db == self._select_db(model_name or "")
