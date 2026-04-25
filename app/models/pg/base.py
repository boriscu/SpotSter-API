from datetime import datetime
from peewee import Model, DateTimeField

from app.init.db_init import db


class BaseModel(Model):
    """
    Abstract base model providing automatic timestamp management.
    All domain models should inherit from this class.
    """

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        """Overrides save to auto-update the updated_at timestamp."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    class Meta:
        database = db
        abstract = True
