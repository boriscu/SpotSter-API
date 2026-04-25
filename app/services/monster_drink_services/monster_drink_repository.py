import os
from typing import Any, Dict, Optional

from flask import abort
from werkzeug.datastructures import FileStorage

from app.models.enums.http_status import HttpStatus
from app.models.pg.monster_drink import MonsterDrink
from app.helpers.slug_generator import generate_slug
from app.services.base_crud_services.base_repository import BaseRepository
from app.services.storage_service import StorageService
from config.app_config import AppConfig


class MonsterDrinkRepository(BaseRepository):
    """Repository for Monster drink data access with S3 image lifecycle management."""

    @staticmethod
    def get_by_flavour(flavour: str) -> Optional[MonsterDrink]:
        """Retrieves a Monster drink by its flavour name."""
        try:
            return MonsterDrink.get(MonsterDrink.flavour == flavour)
        except MonsterDrink.DoesNotExist:
            return None

    @staticmethod
    def _validate_image(image: FileStorage) -> None:
        """Validates image content type and file size against configured limits."""
        if image.content_type not in AppConfig.ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Invalid image type '{image.content_type}'. "
                f"Allowed: {', '.join(AppConfig.ALLOWED_IMAGE_TYPES)}"
            )

        image.seek(0, os.SEEK_END)
        size = image.tell()
        image.seek(0)

        if size > AppConfig.MAX_IMAGE_SIZE_BYTES:
            raise ValueError(
                f"Image too large ({size} bytes). "
                f"Maximum: {AppConfig.MAX_IMAGE_SIZE_BYTES} bytes"
            )

    @staticmethod
    def _upload_image(image: FileStorage, slug: str) -> str:
        """Uploads an image to S3 under the monster-drinks prefix and returns its URL."""
        ext = AppConfig.CONTENT_TYPE_TO_EXT[image.content_type]
        key = f"monster-drinks/{slug}.{ext}"
        return StorageService.upload_file(image.read(), key, image.content_type)

    @staticmethod
    def _delete_image(image_url: str) -> None:
        """Extracts the S3 key from a full image URL and deletes the object."""
        if not image_url:
            return
        bucket = AppConfig.S3_BUCKET_NAME
        prefix = f"{AppConfig.S3_ENDPOINT_URL}/{bucket}/"
        if image_url.startswith(prefix):
            key = image_url[len(prefix):]
            StorageService.delete_file(key)

    @classmethod
    def create_with_image(
        cls, data: Dict[str, Any], image: Optional[FileStorage] = None
    ) -> MonsterDrink:
        """Creates a Monster drink, uploading an image to S3 if provided."""
        if image:
            cls._validate_image(image)
            slug = generate_slug(data.get("name", ""))
            data["image_url"] = cls._upload_image(image, slug)

        return cls.create(MonsterDrink, data)

    @classmethod
    def update_with_image(
        cls, record_id: int, data: Dict[str, Any], image: Optional[FileStorage] = None
    ) -> MonsterDrink:
        """Updates a Monster drink, replacing the S3 image if a new one is provided."""
        old_image_url = None

        if image:
            cls._validate_image(image)
            try:
                existing = MonsterDrink.get_by_id(record_id)
            except MonsterDrink.DoesNotExist:
                abort(HttpStatus.NOT_FOUND.value)
            old_image_url = existing.image_url
            slug = generate_slug(data.get("name", existing.name))
            data["image_url"] = cls._upload_image(image, slug)

        record = cls.update(MonsterDrink, record_id, data)

        if old_image_url:
            try:
                cls._delete_image(old_image_url)
            except RuntimeError:
                pass

        return record

    @classmethod
    def delete_with_image(cls, record_id: int) -> None:
        """Deletes a Monster drink and its associated S3 image."""
        try:
            record = MonsterDrink.get_by_id(record_id)
        except MonsterDrink.DoesNotExist:
            abort(HttpStatus.NOT_FOUND.value)

        image_url = record.image_url
        cls.delete(MonsterDrink, record_id)

        if image_url:
            try:
                cls._delete_image(image_url)
            except RuntimeError:
                pass
