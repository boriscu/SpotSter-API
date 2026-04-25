from peewee import AutoField, TextField, BooleanField

from .base import BaseModel


class AdminUser(BaseModel):
    """
    Database model representing an administrator user.
    Used for authentication and authorization of admin-only API endpoints.
    """

    id = AutoField()
    email = TextField(unique=True, null=False)
    password = TextField(null=False)
    is_admin = BooleanField(default=True)
    is_active = BooleanField(default=True)

    class Meta:
        table_name = "admin_user"
