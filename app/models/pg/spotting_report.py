from peewee import (
    AutoField,
    CharField,
    TextField,
    DoubleField,
    ForeignKeyField,
)

from .base import BaseModel
from .monster_drink import MonsterDrink
from .store import Store

from app.models.enums.spotting_status import SpottingStatus


class SpottingReport(BaseModel):
    """
    Records a user-submitted Monster drink sighting.
    Tracks the uploaded image, geographic coordinates, recognition result,
    and linkage to the matched monster drink and store when successful.
    """

    id = AutoField()
    image_url = TextField(null=True)
    latitude = DoubleField(null=False)
    longitude = DoubleField(null=False)
    status = CharField(
        max_length=20,
        default=SpottingStatus.PENDING.value,
        null=False,
    )
    matched_monster_drink = ForeignKeyField(
        MonsterDrink, backref="spotting_reports", null=True, on_delete="SET NULL"
    )
    matched_store = ForeignKeyField(
        Store, backref="spotting_reports", null=True, on_delete="SET NULL"
    )
    rejection_reason = TextField(null=True)

    class Meta:
        table_name = "spotting_report"
