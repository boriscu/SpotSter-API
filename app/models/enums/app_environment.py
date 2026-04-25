from enum import Enum


class AppEnvironment(Enum):
    """Enum representing the possible application deployment environments."""

    DEV = "DEV"
    STAGING = "STAGING"
    PROD = "PROD"
