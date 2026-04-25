from peewee import (
    AutoField,
    ForeignKeyField,
)

from .base import BaseModel
from .store import Store
from .monster_drink import MonsterDrink


class StoreMonsterAvailability(BaseModel):
    """
    Junction model tracking which Monster drink flavours are available at which stores.
    The unique constraint on (store, monster_drink) prevents duplicate flavour entries per store.
    """

    id = AutoField()
    store = ForeignKeyField(Store, backref="availabilities", on_delete="CASCADE")
    monster_drink = ForeignKeyField(MonsterDrink, backref="availabilities", on_delete="CASCADE")

    class Meta:
        table_name = "store_monster_availability"
        indexes = (
            (("store", "monster_drink"), True),
        )
