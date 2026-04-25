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

    @store_namespace.doc(description="List all stores.")
    @store_namespace.response(HttpStatus.OK.value, "Stores fetched.")
    @store_namespace.marshal_list_with(store_model)
    @jwt_required()
    def get(self):
        """Retrieve all store entries."""
        return StoreRepository.get_all(Store)

    @store_namespace.doc(description="Create a new store.")
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

    @store_namespace.doc(description="Get a single store by ID.")
    @store_namespace.response(HttpStatus.OK.value, "Store fetched.")
    @store_namespace.marshal_with(store_model)
    @jwt_required()
    def get(self, record_id: int):
        """Retrieve a store by its ID."""
        return StoreRepository.get_by_id(Store, record_id)

    @store_namespace.doc(description="Update a store.")
    @store_namespace.expect(store_create_model, validate=True)
    @store_namespace.response(HttpStatus.OK.value, "Store updated.")
    @store_namespace.marshal_with(store_model)
    @jwt_required()
    def put(self, record_id: int):
        """Update an existing store."""
        return StoreRepository.update(Store, record_id, request.get_json(), slug_field=None)

    @store_namespace.doc(description="Delete a store.")
    @store_namespace.response(HttpStatus.OK.value, "Store deleted.")
    @jwt_required()
    def delete(self, record_id: int):
        """Delete a store by its ID."""
        StoreRepository.delete(Store, record_id)
        return HttpResponseGenerator.generate_response(HttpStatus.OK)
