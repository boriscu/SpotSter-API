import os
from config.base_config import BaseConfig


class AppConfig(BaseConfig):
    """
    Application-specific configuration class that handles environment variables.
    Inherits from BaseConfig and loads configurations directly from environment variables.
    """

    APP_ENVIRONMENT = None

    PROPAGATE_EXCEPTIONS = True

    ALLOWED_ORIGINS = [
        "http://localhost:3000",
    ]

    DB_USER = os.getenv("DB_USER")
    DB_NAME = os.getenv("DB_NAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", 5432)

    JWT_SECRET_KEY = None
    JWT_TOKEN_LOCATION = None
    TOKEN_EXPIRATION_TIME = None

    DEBUG_MODE = None

    ADMIN_EMAIL = None
    ADMIN_PASSWORD = None

    SENTRY_DSN = os.getenv("SENTRY_DSN")

    S3_ENDPOINT_URL = None
    S3_ACCESS_KEY = None
    S3_SECRET_KEY = None
    S3_BUCKET_NAME = None
    S3_REGION = None

    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
    MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
    CONTENT_TYPE_TO_EXT = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }

    @classmethod
    def load_config(cls) -> None:
        """
        Loads environment variable-based configurations.
        Populates the class attributes with the configuration data.
        """
        if cls._are_attributes_none():
            cls.APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "DEV")

            cls.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
            cls.JWT_TOKEN_LOCATION = ["headers"]
            cls.TOKEN_EXPIRATION_TIME = os.getenv("TOKEN_EXPIRATION_TIME", "120")

            cls.DEBUG_MODE = os.getenv("DEBUG_MODE") == "True"

            cls.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
            cls.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

            cls.SENTRY_DSN = os.getenv("SENTRY_DSN")

            cls.S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
            cls.S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
            cls.S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
            cls.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "spotster")
            cls.S3_REGION = os.getenv("S3_REGION", "eu-central-1")

            allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
            cls.ALLOWED_ORIGINS = [
                origin.strip() for origin in allowed_origins_env.split(",")
            ]

        super().check_none_values()

    @classmethod
    def _are_attributes_none(cls) -> bool:
        """
        Checks if any of the class attributes are None.

        Returns:
            bool: True if any attribute is None, False otherwise.
        """
        for key in cls.__dict__:
            if not key.startswith("__") and not callable(getattr(cls, key)):
                if getattr(cls, key) is None:
                    return True
        return False
