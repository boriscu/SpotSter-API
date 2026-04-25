from typing import Dict, List, Optional
import math

from app.models.pg.store import Store
from app.models.pg.store_monster_availability import StoreMonsterAvailability
from app.models.pg.monster_drink import MonsterDrink
from app.services.base_crud_services.base_repository import BaseRepository


class StoreRepository(BaseRepository):
    """
    Repository for store data access operations.
    Extends BaseRepository with availability lookups and proximity search.
    """

    @staticmethod
    def get_availability(store_id: int) -> List[Dict]:
        """
        Retrieves all Monster drinks available at a given store.

        Args:
            store_id: The ID of the store.

        Returns:
            List[Dict]: A list of dictionaries containing monster drink details.
        """
        availabilities = (
            StoreMonsterAvailability
            .select(StoreMonsterAvailability, MonsterDrink)
            .join(MonsterDrink)
            .where(StoreMonsterAvailability.store == store_id)
        )

        return [
            {
                "id": availability.monster_drink.id,
                "name": availability.monster_drink.name,
                "flavour": availability.monster_drink.flavour,
                "is_zero_sugar": availability.monster_drink.is_zero_sugar,
                "image_url": availability.monster_drink.image_url,
            }
            for availability in availabilities
        ]

    @staticmethod
    def find_nearest_store(latitude: float, longitude: float) -> Optional[Store]:
        """
        Finds the nearest store to the given coordinates using Haversine approximation.
        Only considers stores within a 1km radius.

        Args:
            latitude: The latitude coordinate.
            longitude: The longitude coordinate.

        Returns:
            Optional[Store]: The nearest Store instance, or None if no store is within range.
        """
        maximum_distance_km = 1.0
        nearest_store = None
        minimum_distance = float("inf")

        for store in Store.select():
            distance = StoreRepository._haversine_distance(
                latitude, longitude, store.latitude, store.longitude
            )
            if distance < minimum_distance and distance <= maximum_distance_km:
                minimum_distance = distance
                nearest_store = store

        return nearest_store

    @staticmethod
    def _haversine_distance(
        latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float
    ) -> float:
        """
        Calculates the great-circle distance between two points on Earth.

        Args:
            latitude_1: Latitude of the first point in degrees.
            longitude_1: Longitude of the first point in degrees.
            latitude_2: Latitude of the second point in degrees.
            longitude_2: Longitude of the second point in degrees.

        Returns:
            float: Distance in kilometres.
        """
        earth_radius_km = 6371.0

        latitude_1_rad = math.radians(latitude_1)
        latitude_2_rad = math.radians(latitude_2)
        delta_latitude = math.radians(latitude_2 - latitude_1)
        delta_longitude = math.radians(longitude_2 - longitude_1)

        haversine_a = (
            math.sin(delta_latitude / 2) ** 2
            + math.cos(latitude_1_rad) * math.cos(latitude_2_rad)
            * math.sin(delta_longitude / 2) ** 2
        )
        haversine_c = 2 * math.atan2(math.sqrt(haversine_a), math.sqrt(1 - haversine_a))

        return earth_radius_km * haversine_c
