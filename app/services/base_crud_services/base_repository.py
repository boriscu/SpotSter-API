from typing import Any, Dict, List, Optional, Type
from flask import abort

from peewee import Model

from app.models.enums.http_status import HttpStatus
from app.helpers.slug_generator import generate_slug

from app.services.admin_auth_services.admin_auth_service import AdminAuthService


class BaseRepository:
    """
    Generic CRUD repository providing standard create, read, update, delete,
    and list operations for any Peewee model.

    All mutating operations enforce admin privileges by default.
    Subclasses can override methods for entity-specific behavior.
    """

    @staticmethod
    def get_all(model: Type[Model]) -> List[Model]:
        """
        Retrieves all records for the given model.

        Args:
            model: The Peewee model class to query.

        Returns:
            List[Model]: A list of all model instances.
        """
        return list(model.select())

    @staticmethod
    def get_by_id(model: Type[Model], record_id: int) -> Model:
        """
        Retrieves a single record by its ID.

        Args:
            model: The Peewee model class.
            record_id: The primary key of the record.

        Returns:
            The model instance.

        Raises:
            HTTPException: 404 if the record does not exist.
        """
        try:
            return model.get_by_id(record_id)
        except model.DoesNotExist:
            abort(HttpStatus.NOT_FOUND.value)

    @staticmethod
    def create(
        model: Type[Model],
        data: Dict[str, Any],
        slug_field: Optional[str] = "name",
    ) -> Model:
        """
        Creates a new record. Auto-generates a slug from the slug_field if the
        model has a 'slug' column.

        Args:
            model: The Peewee model class.
            data: Dictionary of field values.
            slug_field: The field name to generate the slug from. Set to None to skip.

        Returns:
            The newly created model instance.
        """
        AdminAuthService.check_if_admin_and_raise()

        if slug_field and slug_field in data and hasattr(model, "slug"):
            data["slug"] = generate_slug(data[slug_field])

        record = model.create(**data)
        return record

    @staticmethod
    def update(
        model: Type[Model],
        record_id: int,
        data: Dict[str, Any],
        slug_field: Optional[str] = "name",
    ) -> Model:
        """
        Updates an existing record by ID. Re-generates the slug if the
        slug source field has changed.

        Args:
            model: The Peewee model class.
            record_id: The primary key of the record to update.
            data: Dictionary of field values to update.
            slug_field: The field name to regenerate the slug from. Set to None to skip.

        Returns:
            The updated model instance.

        Raises:
            HTTPException: 404 if the record does not exist.
        """
        AdminAuthService.check_if_admin_and_raise()

        try:
            record = model.get_by_id(record_id)
        except model.DoesNotExist:
            abort(HttpStatus.NOT_FOUND.value)

        if slug_field and slug_field in data and hasattr(model, "slug"):
            data["slug"] = generate_slug(data[slug_field])

        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        record.save()
        return record

    @staticmethod
    def delete(model: Type[Model], record_id: int) -> None:
        """
        Deletes a record by its ID.

        Args:
            model: The Peewee model class.
            record_id: The primary key of the record to delete.

        Raises:
            HTTPException: 404 if the record does not exist.
        """
        AdminAuthService.check_if_admin_and_raise()

        try:
            record = model.get_by_id(record_id)
        except model.DoesNotExist:
            abort(HttpStatus.NOT_FOUND.value)

        record.delete_instance()
