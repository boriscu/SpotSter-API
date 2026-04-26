from peewee import (
    AutoField,
    CharField,
    TextField,
    IntegerField,
    DecimalField,
    BooleanField,
)

from .base import BaseModel


class MonsterDrink(BaseModel):
    """
    Ground truth model representing a known Monster Energy drink variant.
    Contains canonical information used for identification and display.
    """

    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)
    flavour = CharField(max_length=100, unique=True, null=False)
    slug = CharField(max_length=100, unique=True, null=False)
    description = TextField(null=True)
    calories = IntegerField(null=True)
    sugar_grams = DecimalField(decimal_places=1, null=True)
    caffeine_mg = IntegerField(null=True)
    is_zero_sugar = BooleanField(default=False)
    image_url = TextField(null=True)
    tag = IntegerField(null=True)

    class Meta:
        table_name = "monster_drink"
