from peewee import (
    AutoField,
    CharField,
    TextField,
    DoubleField,
)

from .base import BaseModel


class Store(BaseModel):
    """
    Represents a physical retail store where Monster drinks can be spotted.
    Stores are geo-located via latitude and longitude coordinates.
    """

    id = AutoField()
    name = CharField(max_length=200, null=False)
    address = TextField(null=True)
    latitude = DoubleField(null=False)
    longitude = DoubleField(null=False)

    class Meta:
        table_name = "store"
