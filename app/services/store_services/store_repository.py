from datetime import datetime
from typing import Any, Dict, List, Optional
import math

from app.models.pg.store import Store
from app.models.pg.store_monster_availability import StoreMonsterAvailability
from app.models.pg.monster_drink import MonsterDrink
from app.models.pg.spotting_report import SpottingReport
from app.services.base_crud_services.base_repository import BaseRepository


class StoreRepository(BaseRepository):
    """Repository for store data access with proximity search, filtering, and detail views."""

    @staticmethod
    def get_availability(store_id: int) -> List[Dict]:
        """Retrieves all Monster drinks available at a given store, sorted by most recently spotted.

        Args:
            store_id: The ID of the store.

        Returns:
            List[Dict]: A list of dictionaries containing monster drink details and last spotted time.
        """
        availabilities = (
            StoreMonsterAvailability
            .select(StoreMonsterAvailability, MonsterDrink)
            .join(MonsterDrink)
            .where(StoreMonsterAvailability.store == store_id)
            .order_by(StoreMonsterAvailability.updated_at.desc())
        )

        return [
            {
                "id": a.monster_drink.id,
                "name": a.monster_drink.name,
                "flavour": a.monster_drink.flavour,
                "slug": a.monster_drink.slug,
                "is_zero_sugar": a.monster_drink.is_zero_sugar,
                "image_url": a.monster_drink.image_url,
                "tag": a.monster_drink.tag,
                "last_spotted_at": str(a.updated_at) if a.updated_at else None,
            }
            for a in availabilities
        ]

    @classmethod
    def get_stores(
        cls,
        sw_lat: Optional[float] = None,
        sw_lng: Optional[float] = None,
        ne_lat: Optional[float] = None,
        ne_lng: Optional[float] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        flavour_slugs: Optional[List[str]] = None,
        tags: Optional[List[int]] = None,
        spotted_since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Returns stores within the map viewport, with filtering and pagination.

        Args:
            sw_lat: Southwest corner latitude of the visible map area.
            sw_lng: Southwest corner longitude of the visible map area.
            ne_lat: Northeast corner latitude of the visible map area.
            ne_lng: Northeast corner longitude of the visible map area.
            center_lat: Map center latitude for distance sorting within the viewport.
            center_lng: Map center longitude for distance sorting within the viewport.
            limit: Maximum number of stores to return per page.
            offset: Number of stores to skip for pagination.
            search: Free-text search across store names and monster names/flavours.
            flavour_slugs: List of monster slugs to filter by.
            tags: List of MonsterTag integer values to filter by.
            spotted_since: Only include stores with spottings after this datetime.

        Returns:
            Dict[str, Any]: Paginated response with stores, total count, limit, and offset.
        """
        store_ids = cls._get_filtered_store_ids(search, flavour_slugs, tags, spotted_since)

        if store_ids is not None and not store_ids:
            return {"stores": [], "total": 0, "limit": limit, "offset": offset}

        query = Store.select()
        if store_ids is not None:
            query = query.where(Store.id.in_(store_ids))

        has_bounds = all(v is not None for v in [sw_lat, sw_lng, ne_lat, ne_lng])
        if has_bounds:
            if sw_lng <= ne_lng:
                query = query.where(
                    (Store.latitude >= sw_lat)
                    & (Store.latitude <= ne_lat)
                    & (Store.longitude >= sw_lng)
                    & (Store.longitude <= ne_lng)
                )
            else:
                query = query.where(
                    (Store.latitude >= sw_lat)
                    & (Store.latitude <= ne_lat)
                    & ((Store.longitude >= sw_lng) | (Store.longitude <= ne_lng))
                )

        stores = list(query)
        total = len(stores)

        has_center = center_lat is not None and center_lng is not None
        if has_center:
            stores_ranked = [
                (store, cls._haversine_distance(center_lat, center_lng, store.latitude, store.longitude))
                for store in stores
            ]
            stores_ranked.sort(key=lambda x: x[1])
        else:
            stores_ranked = [(store, None) for store in sorted(stores, key=lambda s: s.name)]

        page = stores_ranked[offset:offset + limit]

        return {
            "stores": [
                {
                    "id": store.id,
                    "name": store.name,
                    "address": store.address,
                    "latitude": store.latitude,
                    "longitude": store.longitude,
                    "distance_km": round(distance, 2) if distance is not None else None,
                    "available_monsters": cls.get_availability(store.id),
                }
                for store, distance in page
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    @classmethod
    def _get_filtered_store_ids(
        cls,
        search: Optional[str],
        flavour_slugs: Optional[List[str]],
        tags: Optional[List[int]],
        spotted_since: Optional[datetime],
    ) -> Optional[set]:
        """Applies search, flavour, tag, and recency filters, returning matching store IDs.

        Args:
            search: Free-text search term for store name or monster name/flavour.
            flavour_slugs: Monster slugs to require.
            tags: MonsterTag integer values to require.
            spotted_since: Minimum updated_at for availability rows.

        Returns:
            Optional[set]: Set of matching store IDs, or None if no filters were applied.
        """
        if not search and not flavour_slugs and not tags and not spotted_since:
            return None

        candidate_ids = None

        if search:
            by_name = set(
                s.id for s in Store.select(Store.id).where(Store.name.icontains(search))
            )
            by_monster = set(
                a.store_id for a in (
                    StoreMonsterAvailability
                    .select(StoreMonsterAvailability.store)
                    .join(MonsterDrink)
                    .where(
                        MonsterDrink.name.icontains(search)
                        | MonsterDrink.flavour.icontains(search)
                    )
                )
            )
            candidate_ids = by_name | by_monster

        if flavour_slugs:
            by_flavour = set(
                a.store_id for a in (
                    StoreMonsterAvailability
                    .select(StoreMonsterAvailability.store)
                    .join(MonsterDrink)
                    .where(MonsterDrink.slug.in_(flavour_slugs))
                )
            )
            candidate_ids = by_flavour if candidate_ids is None else candidate_ids & by_flavour

        if tags:
            by_tag = set(
                a.store_id for a in (
                    StoreMonsterAvailability
                    .select(StoreMonsterAvailability.store)
                    .join(MonsterDrink)
                    .where(MonsterDrink.tag.in_(tags))
                )
            )
            candidate_ids = by_tag if candidate_ids is None else candidate_ids & by_tag

        if spotted_since:
            by_recency = set(
                a.store_id for a in (
                    StoreMonsterAvailability
                    .select(StoreMonsterAvailability.store)
                    .where(StoreMonsterAvailability.updated_at >= spotted_since)
                )
            )
            candidate_ids = by_recency if candidate_ids is None else candidate_ids & by_recency

        return candidate_ids

    @staticmethod
    def get_store_detail(store_id: int) -> Dict[str, Any]:
        """Returns full store detail with available monsters, recent spottings, and counts.

        Args:
            store_id: The ID of the store.

        Returns:
            Dict[str, Any]: Store info, available monsters, recent spotting images, and aggregate counts.
        """
        store = Store.get_by_id(store_id)

        availabilities = (
            StoreMonsterAvailability
            .select(StoreMonsterAvailability, MonsterDrink)
            .join(MonsterDrink)
            .where(StoreMonsterAvailability.store == store_id)
            .order_by(StoreMonsterAvailability.updated_at.desc())
        )

        recent_spottings = (
            SpottingReport
            .select(SpottingReport, MonsterDrink)
            .join(MonsterDrink, on=(SpottingReport.matched_monster_drink == MonsterDrink.id))
            .where(SpottingReport.matched_store == store_id)
            .order_by(SpottingReport.created_at.desc())
            .limit(10)
        )

        total_spottings = (
            SpottingReport
            .select()
            .where(SpottingReport.matched_store == store_id)
            .count()
        )

        return {
            "id": store.id,
            "name": store.name,
            "address": store.address,
            "latitude": store.latitude,
            "longitude": store.longitude,
            "flavour_count": availabilities.count(),
            "total_spottings": total_spottings,
            "available_monsters": [
                {
                    "id": a.monster_drink.id,
                    "name": a.monster_drink.name,
                    "flavour": a.monster_drink.flavour,
                    "slug": a.monster_drink.slug,
                    "is_zero_sugar": a.monster_drink.is_zero_sugar,
                    "image_url": a.monster_drink.image_url,
                    "tag": a.monster_drink.tag,
                    "last_spotted_at": str(a.updated_at) if a.updated_at else None,
                }
                for a in availabilities
            ],
            "recent_spottings": [
                {
                    "id": r.id,
                    "image_url": r.image_url,
                    "created_at": str(r.created_at),
                    "matched_monster": {
                        "id": r.matched_monster_drink.id,
                        "name": r.matched_monster_drink.name,
                        "flavour": r.matched_monster_drink.flavour,
                        "image_url": r.matched_monster_drink.image_url,
                    },
                }
                for r in recent_spottings
            ],
        }

    @staticmethod
    def find_nearest_store(latitude: float, longitude: float) -> Optional[Store]:
        """Finds the nearest store within 1km of the given coordinates.

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
        """Calculates the great-circle distance in kilometres between two coordinate points.

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
