from enum import Enum


class SpottingStatus(Enum):
    """Enum representing the processing status of a spotting report."""

    PENDING = "pending"
    MATCHED = "matched"
    REJECTED = "rejected"
