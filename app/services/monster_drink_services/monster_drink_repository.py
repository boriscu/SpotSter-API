from typing import Optional

from app.models.pg.monster_drink import MonsterDrink
from app.services.base_crud_services.base_repository import BaseRepository


class MonsterDrinkRepository(BaseRepository):
    """
    Repository for Monster drink ground truth data access operations.
    Extends BaseRepository with flavour-specific lookups.
    """

    @staticmethod
    def get_by_flavour(flavour: str) -> Optional[MonsterDrink]:
        """
        Retrieves a Monster drink by its flavour name.

        Args:
            flavour: The flavour name to search for (case-insensitive).

        Returns:
            Optional[MonsterDrink]: The matching MonsterDrink instance, or None if not found.
        """
        try:
            return MonsterDrink.get(MonsterDrink.flavour == flavour)
        except MonsterDrink.DoesNotExist:
            return None
