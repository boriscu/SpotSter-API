from flask_restx import Resource, fields

from app.models.enums.http_status import HttpStatus
from app.models.pg.monster_drink import MonsterDrink
from app.models.pg.store import Store
from app.services.store_services.store_repository import StoreRepository

from . import public_namespace


monster_public_model = public_namespace.model("MonsterDrinkPublic", {
    "id": fields.Integer(description="Monster drink ID"),
    "name": fields.String(description="Product name"),
    "flavour": fields.String(description="Flavour name"),
    "slug": fields.String(description="URL-friendly slug"),
    "description": fields.String(description="Product description"),
    "calories": fields.Integer(description="Calories per serving"),
    "sugar_grams": fields.Float(description="Sugar content in grams"),
    "caffeine_mg": fields.Integer(description="Caffeine content in milligrams"),
    "is_zero_sugar": fields.Boolean(description="Whether the drink is zero sugar"),
    "image_url": fields.String(description="Ground truth image URL"),
})

store_public_model = public_namespace.model("StorePublic", {
    "id": fields.Integer(description="Store ID"),
    "name": fields.String(description="Store name"),
    "address": fields.String(description="Store address"),
    "latitude": fields.Float(description="Latitude coordinate"),
    "longitude": fields.Float(description="Longitude coordinate"),
})

availability_model = public_namespace.model("Availability", {
    "id": fields.Integer(description="Monster drink ID"),
    "name": fields.String(description="Product name"),
    "flavour": fields.String(description="Flavour name"),
    "is_zero_sugar": fields.Boolean(description="Whether the drink is zero sugar"),
    "image_url": fields.String(description="Ground truth image URL"),
})

store_detail_model = public_namespace.model("StoreDetail", {
    "id": fields.Integer(description="Store ID"),
    "name": fields.String(description="Store name"),
    "address": fields.String(description="Store address"),
    "latitude": fields.Float(description="Latitude coordinate"),
    "longitude": fields.Float(description="Longitude coordinate"),
    "available_monsters": fields.List(fields.Nested(availability_model)),
})


@public_namespace.route("/monsters/", methods=["GET"])
class PublicMonsterListEndpoint(Resource):
    """Public endpoint for browsing the Monster drink catalogue."""

    @public_namespace.doc(description="List all Monster drinks in the catalogue.")
    @public_namespace.response(HttpStatus.OK.value, "Monsters fetched.")
    @public_namespace.marshal_list_with(monster_public_model)
    def get(self):
        """Retrieve all Monster drink entries (public, no auth required)."""
        return list(MonsterDrink.select())


@public_namespace.route("/monsters/<int:monster_id>", methods=["GET"])
class PublicMonsterDetailEndpoint(Resource):
    """Public endpoint for viewing a single Monster drink."""

    @public_namespace.doc(description="Get a single Monster drink by ID.")
    @public_namespace.response(HttpStatus.OK.value, "Monster drink fetched.")
    @public_namespace.marshal_with(monster_public_model)
    def get(self, monster_id: int):
        """Retrieve a Monster drink by its ID (public, no auth required)."""
        return MonsterDrink.get_by_id(monster_id)


@public_namespace.route("/stores/", methods=["GET"])
class PublicStoreListEndpoint(Resource):
    """Public endpoint for browsing stores."""

    @public_namespace.doc(description="List all stores.")
    @public_namespace.response(HttpStatus.OK.value, "Stores fetched.")
    @public_namespace.marshal_list_with(store_public_model)
    def get(self):
        """Retrieve all store entries (public, no auth required)."""
        return list(Store.select())


@public_namespace.route("/stores/<int:store_id>", methods=["GET"])
class PublicStoreDetailEndpoint(Resource):
    """Public endpoint for viewing a single store with its available Monster drinks."""

    @public_namespace.doc(description="Get a store with its available Monster drinks.")
    @public_namespace.response(HttpStatus.OK.value, "Store fetched.")
    def get(self, store_id: int):
        """Retrieve a store and its available Monster drinks (public, no auth required)."""
        store = Store.get_by_id(store_id)
        available_monsters = StoreRepository.get_availability(store_id)

        return {
            "id": store.id,
            "name": store.name,
            "address": store.address,
            "latitude": store.latitude,
            "longitude": store.longitude,
            "available_monsters": available_monsters,
        }
