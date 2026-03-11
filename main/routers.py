"""Routers for the database."""

from typing import Any

from django.db import models


class Router:
    """A router to control where models are read from."""

    route_app_labels = "main"

    def _select_db(self, model_name: str) -> str | None:
        """Internal function to select the right database."""
        if model_name.lower().startswith("imap"):
            return "imap"
        if model_name.lower().startswith("so"):
            return "so"
        return None

    def db_for_read(  # type: ignore[explicit-any]
        self,
        model: models.Model,
        **hints: Any,
    ) -> str | None:
        """Select the database to read."""
        return self._select_db(model._meta.model_name or "")

    def db_for_write(  # type: ignore[explicit-any]
        self,
        model: models.Model,
        **hints: Any,
    ) -> str | None:
        """Select the database to read."""
        return self._select_db(model._meta.model_name or "")

    def allow_migrate(  # type: ignore[explicit-any]
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: Any,
    ) -> bool | None:
        """Make sure the models appear in the right db during migrations."""
        if app_label in self.route_app_labels:
            return db == self._select_db(model_name or "")
        return None
