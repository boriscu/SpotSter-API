import uuid
from typing import Dict, Any
from io import BytesIO

from PIL import Image
from peewee import IntegrityError

from app.models.pg.spotting_report import SpottingReport
from app.models.pg.store_monster_availability import StoreMonsterAvailability
from app.models.enums.spotting_status import SpottingStatus

from app.services.storage_service import StorageService
from app.services.store_services.store_repository import StoreRepository
from app.services.spotting_services.monster_recognition_engine import MonsterRecognitionEngine

from app.init.logger_setup import LoggerSetup


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


class SpottingReportService:
    """
    Facade orchestrating the full spotting report flow.
    Validates the uploaded image, stores it in S3, runs recognition,
    matches to the nearest store, and creates the availability record.
    """

    _recognition_engine = None

    @classmethod
    def _get_recognition_engine(cls) -> MonsterRecognitionEngine:
        """Lazily initializes the recognition engine so config is loaded before provider selection."""
        if cls._recognition_engine is None:
            cls._recognition_engine = MonsterRecognitionEngine()
        return cls._recognition_engine

    @classmethod
    def process_spotting(
        cls,
        file_data: bytes,
        filename: str,
        content_type: str,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Processes a complete spotting submission from image upload through recognition.

        Args:
            file_data: The raw image bytes uploaded by the user.
            filename: The original filename of the uploaded image.
            content_type: The MIME type of the uploaded file.
            latitude: The latitude coordinate where the photo was taken.
            longitude: The longitude coordinate where the photo was taken.

        Returns:
            Dict[str, Any]: A dictionary containing the processing result including
                            status, matched monster info, and store info if applicable.

        Raises:
            ValueError: If the image fails validation (wrong type, too large, or corrupt).
        """
        logger = LoggerSetup.get_logger("general")

        cls._validate_image(file_data, filename)

        recognition_result = cls._get_recognition_engine().identify(file_data)

        if not recognition_result.is_match:
            report = SpottingReport.create(
                latitude=latitude,
                longitude=longitude,
                status=SpottingStatus.REJECTED.value,
                rejection_reason=recognition_result.rejection_reason,
            )

            logger.info(f"Spotting rejected: {recognition_result.rejection_reason}")

            return cls._build_response(report)

        image_url = cls._upload_image(file_data, filename, content_type)

        nearest_store = StoreRepository.find_nearest_store(latitude, longitude)

        if nearest_store:
            try:
                StoreMonsterAvailability.create(
                    store=nearest_store,
                    monster_drink=recognition_result.matched_monster_drink,
                )
                logger.info(
                    f"Availability created: {recognition_result.matched_monster_drink.name} "
                    f"at {nearest_store.name}"
                )
            except IntegrityError:
                availability = StoreMonsterAvailability.get(
                    (StoreMonsterAvailability.store == nearest_store)
                    & (StoreMonsterAvailability.monster_drink == recognition_result.matched_monster_drink)
                )
                availability.save()
                logger.info(
                    f"Availability re-spotted: {recognition_result.matched_monster_drink.name} "
                    f"at {nearest_store.name} — updated_at bumped."
                )

        report = SpottingReport.create(
            image_url=image_url,
            latitude=latitude,
            longitude=longitude,
            status=SpottingStatus.MATCHED.value,
            matched_monster_drink=recognition_result.matched_monster_drink,
            matched_store=nearest_store,
        )

        logger.info(f"Spotting matched: report {report.id}")

        return cls._build_response(report)

    @classmethod
    def _validate_image(cls, file_data: bytes, filename: str) -> None:
        """
        Validates the uploaded image for file type, size, and integrity.

        Args:
            file_data: The raw image bytes.
            filename: The original filename.

        Raises:
            ValueError: If validation fails.
        """
        if not filename or "." not in filename:
            raise ValueError("Invalid filename.")

        extension = filename.rsplit(".", 1)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        if len(file_data) > MAX_FILE_SIZE_BYTES:
            raise ValueError("File too large. Maximum size is 10MB.")

        try:
            image = Image.open(BytesIO(file_data))
            image.verify()
        except Exception:
            raise ValueError(
                "Image appears to be corrupted or unreadable. Please upload a valid image."
            )

    @classmethod
    def _upload_image(cls, file_data: bytes, filename: str, content_type: str) -> str:
        """
        Uploads the image to S3 storage with a unique key.

        Args:
            file_data: The raw image bytes.
            filename: The original filename.
            content_type: The MIME type.

        Returns:
            str: The S3 URL of the uploaded image.
        """
        extension = filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{extension}"
        key = f"spottings/{unique_name}"

        return StorageService.upload_file(file_data, key, content_type)

    @classmethod
    def _build_response(cls, report: SpottingReport) -> Dict[str, Any]:
        """
        Builds a standardised response dictionary from a spotting report.

        Args:
            report: The SpottingReport instance.

        Returns:
            Dict[str, Any]: A response dictionary with report details.
        """
        response = {
            "id": report.id,
            "image_url": report.image_url,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "status": report.status,
            "created_at": str(report.created_at),
        }

        if report.status == SpottingStatus.MATCHED.value and report.matched_monster_drink:
            response["matched_monster"] = {
                "id": report.matched_monster_drink.id,
                "name": report.matched_monster_drink.name,
                "flavour": report.matched_monster_drink.flavour,
                "image_url": report.matched_monster_drink.image_url,
            }

        if report.matched_store:
            response["matched_store"] = {
                "id": report.matched_store.id,
                "name": report.matched_store.name,
            }

        if report.status == SpottingStatus.REJECTED.value:
            response["rejection_reason"] = report.rejection_reason

        return response
