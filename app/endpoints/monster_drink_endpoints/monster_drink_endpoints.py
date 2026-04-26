from flask_jwt_extended import jwt_required
from flask_restx import Resource, fields, inputs
from werkzeug.datastructures import FileStorage

from app.helpers.http_response_generator import HttpResponseGenerator
from app.models.enums.http_status import HttpStatus
from app.models.pg.monster_drink import MonsterDrink
from app.services.monster_drink_services.monster_drink_repository import MonsterDrinkRepository

from . import monster_drink_namespace


monster_drink_model = monster_drink_namespace.model("MonsterDrink", {
    "id": fields.Integer(readonly=True, description="Monster drink ID"),
    "name": fields.String(required=True, description="Product name"),
    "flavour": fields.String(required=True, description="Flavour name"),
    "slug": fields.String(readonly=True, description="URL-friendly slug"),
    "description": fields.String(description="Product description"),
    "calories": fields.Integer(description="Calories per serving"),
    "sugar_grams": fields.Float(description="Sugar content in grams"),
    "caffeine_mg": fields.Integer(description="Caffeine content in milligrams"),
    "is_zero_sugar": fields.Boolean(description="Whether the drink is zero sugar"),
    "image_url": fields.String(description="Ground truth image URL"),
    "tag": fields.Integer(description="Product line tag (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special)"),
    "created_at": fields.DateTime(readonly=True),
    "updated_at": fields.DateTime(readonly=True),
})

monster_drink_parser = monster_drink_namespace.parser()
monster_drink_parser.add_argument("name", type=str, required=True, location="form", help="Product name")
monster_drink_parser.add_argument("flavour", type=str, required=True, location="form", help="Flavour name")
monster_drink_parser.add_argument("description", type=str, location="form", help="Product description")
monster_drink_parser.add_argument("calories", type=int, location="form", help="Calories per serving")
monster_drink_parser.add_argument("sugar_grams", type=float, location="form", help="Sugar content in grams")
monster_drink_parser.add_argument("caffeine_mg", type=int, location="form", help="Caffeine content in milligrams")
monster_drink_parser.add_argument("is_zero_sugar", type=inputs.boolean, location="form", help="Whether the drink is zero sugar")
monster_drink_parser.add_argument("tag", type=int, location="form", help="Product line tag (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special)")
monster_drink_parser.add_argument("image", type=FileStorage, location="files", help="Product image (JPEG, PNG, or WebP, max 5MB)")


@monster_drink_namespace.route("/", methods=["GET", "POST"])
class MonsterDrinkListEndpoint(Resource):
    """Admin endpoint for listing and creating Monster drinks."""

    @monster_drink_namespace.doc(description="List all Monster drinks.")
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monsters fetched.")
    @monster_drink_namespace.marshal_list_with(monster_drink_model)
    @jwt_required()
    def get(self):
        """Retrieve all Monster drink entries."""
        return MonsterDrinkRepository.get_all(MonsterDrink)

    @monster_drink_namespace.doc(description="Create a new Monster drink with optional image upload.")
    @monster_drink_namespace.expect(monster_drink_parser)
    @monster_drink_namespace.response(HttpStatus.CREATED.value, "Monster drink created.")
    @monster_drink_namespace.marshal_with(monster_drink_model)
    @jwt_required()
    def post(self):
        """Create a new Monster drink entry."""
        args = monster_drink_parser.parse_args()
        image = args.pop("image", None)
        data = {k: v for k, v in args.items() if v is not None}
        record = MonsterDrinkRepository.create_with_image(data, image)
        return record, HttpStatus.CREATED.value


@monster_drink_namespace.route("/<int:record_id>", methods=["GET", "PUT", "DELETE"])
class MonsterDrinkDetailEndpoint(Resource):
    """Admin endpoint for retrieving, updating, and deleting a single Monster drink."""

    @monster_drink_namespace.doc(description="Get a single Monster drink by ID.")
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monster drink fetched.")
    @monster_drink_namespace.marshal_with(monster_drink_model)
    @jwt_required()
    def get(self, record_id: int):
        """Retrieve a Monster drink by its ID."""
        return MonsterDrinkRepository.get_by_id(MonsterDrink, record_id)

    @monster_drink_namespace.doc(description="Update a Monster drink with optional image replacement.")
    @monster_drink_namespace.expect(monster_drink_parser)
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monster drink updated.")
    @monster_drink_namespace.marshal_with(monster_drink_model)
    @jwt_required()
    def put(self, record_id: int):
        """Update an existing Monster drink."""
        args = monster_drink_parser.parse_args()
        image = args.pop("image", None)
        data = {k: v for k, v in args.items() if v is not None}
        return MonsterDrinkRepository.update_with_image(record_id, data, image)

    @monster_drink_namespace.doc(description="Delete a Monster drink and its image.")
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monster drink deleted.")
    @jwt_required()
    def delete(self, record_id: int):
        """Delete a Monster drink by its ID."""
        MonsterDrinkRepository.delete_with_image(record_id)
        return HttpResponseGenerator.generate_response(HttpStatus.OK)
