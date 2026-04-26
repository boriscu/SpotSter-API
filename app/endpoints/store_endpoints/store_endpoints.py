from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Resource, fields

from app.helpers.http_response_generator import HttpResponseGenerator
from app.models.enums.http_status import HttpStatus
from app.models.pg.store import Store
from app.services.store_services.store_repository import StoreRepository

from . import store_namespace


store_model = store_namespace.model("Store", {
    "id": fields.Integer(readonly=True, description="Store ID"),
    "name": fields.String(required=True, description="Store name"),
    "address": fields.String(description="Store address"),
    "latitude": fields.Float(required=True, description="Latitude coordinate"),
    "longitude": fields.Float(required=True, description="Longitude coordinate"),
    "created_at": fields.DateTime(readonly=True),
    "updated_at": fields.DateTime(readonly=True),
})

store_create_model = store_namespace.model("StoreCreate", {
    "name": fields.String(required=True, description="Store name"),
    "address": fields.String(description="Store address"),
    "latitude": fields.Float(required=True, description="Latitude coordinate"),
    "longitude": fields.Float(required=True, description="Longitude coordinate"),
})


@store_namespace.route("/", methods=["GET", "POST"])
class StoreListEndpoint(Resource):
    """Admin endpoint for listing and creating stores."""

    @store_namespace.doc(
        description=(
            "Returns all store entries in the database.\n\n"
            "This is the admin view — returns raw store records without availability data or distance calculations. "
            "For the public-facing store list with filtering and bounding box support, "
            "use `GET /api/v1/public/stores/`.\n\n"
            "**Example:**\n"
            "`GET /api/v1/admin/stores/`"
        ),
    )
    @store_namespace.response(HttpStatus.OK.value, "Stores fetched.")
    @store_namespace.marshal_list_with(store_model)
    @jwt_required()
    def get(self):
        """Retrieve all store entries."""
        return StoreRepository.get_all(Store)

    @store_namespace.doc(
        description=(
            "Create a new store entry.\n\n"
            "**Request body:** JSON with `name`, `latitude`, and `longitude` (required), "
            "plus optional `address`.\n\n"
            "Stores represent physical locations where Monster drinks can be spotted. "
            "Coordinates are used for proximity search and map display on the public endpoints.\n\n"
            "**Example:**\n"
            '`POST /api/v1/admin/stores/` with `{"name": "Maxi", "address": "Bulevar Kralja Aleksandra 50", '
            '"latitude": 44.8125, "longitude": 20.4612}`'
        ),
    )
    @store_namespace.expect(store_create_model, validate=True)
    @store_namespace.response(HttpStatus.CREATED.value, "Store created.")
    @store_namespace.marshal_with(store_model)
    @jwt_required()
    def post(self):
        """Create a new store entry."""
        record = StoreRepository.create(Store, request.get_json(), slug_field=None)
        return record, HttpStatus.CREATED.value


@store_namespace.route("/<int:record_id>", methods=["GET", "PUT", "DELETE"])
class StoreDetailEndpoint(Resource):
    """Admin endpoint for retrieving, updating, and deleting a single store."""

    @store_namespace.doc(
        description=(
            "Retrieve a single store by its database ID.\n\n"
            "Returns the raw store record. For the public detail view with available monsters "
            "and recent spottings, use `GET /api/v1/public/stores/{store_id}`.\n\n"
            "**Returns 404** if no store exists with the given ID.\n\n"
            "**Example:**\n"
            "`GET /api/v1/admin/stores/5`"
        ),
    )
    @store_namespace.response(HttpStatus.OK.value, "Store fetched.")
    @store_namespace.marshal_with(store_model)
    @jwt_required()
    def get(self, record_id: int):
        """Retrieve a store by its ID."""
        return StoreRepository.get_by_id(Store, record_id)

    @store_namespace.doc(
        description=(
            "Update an existing store entry.\n\n"
            "**Request body:** JSON with the fields to update. All fields from the create model "
            "are accepted (`name`, `address`, `latitude`, `longitude`).\n\n"
            "**Returns 404** if no store exists with the given ID.\n\n"
            "**Example:**\n"
            '`PUT /api/v1/admin/stores/5` with `{"address": "Bulevar Kralja Aleksandra 52"}`'
        ),
    )
    @store_namespace.expect(store_create_model, validate=True)
    @store_namespace.response(HttpStatus.OK.value, "Store updated.")
    @store_namespace.marshal_with(store_model)
    @jwt_required()
    def put(self, record_id: int):
        """Update an existing store."""
        return StoreRepository.update(Store, record_id, request.get_json(), slug_field=None)

    @store_namespace.doc(
        description=(
            "Delete a store by its ID.\n\n"
            "Removes the store record from the database. This also affects any availability "
            "and spotting records linked to this store.\n\n"
            "**Returns 404** if no store exists with the given ID.\n\n"
            "**Example:**\n"
            "`DELETE /api/v1/admin/stores/5`"
        ),
    )
    @store_namespace.response(HttpStatus.OK.value, "Store deleted.")
    @jwt_required()
    def delete(self, record_id: int):
        """Delete a store by its ID."""
        StoreRepository.delete(Store, record_id)
        return HttpResponseGenerator.generate_response(HttpStatus.OK)
