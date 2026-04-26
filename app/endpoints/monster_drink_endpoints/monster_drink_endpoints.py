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

    @monster_drink_namespace.doc(
        description="Returns all Monster drink entries in the ground truth database, including image URLs and product line tags.",
    )
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monsters fetched.")
    @monster_drink_namespace.marshal_list_with(monster_drink_model)
    @jwt_required()
    def get(self):
        """Retrieve all Monster drink entries."""
        return MonsterDrinkRepository.get_all(MonsterDrink)

    @monster_drink_namespace.doc(
        description=(
            "Create a new Monster drink entry in the ground truth database.\n\n"
            "**Request format:** `multipart/form-data` with product fields and an optional image file.\n\n"
            "**Required fields:** `name`, `flavour`.\n\n"
            "**Optional fields:** `description`, `calories`, `sugar_grams`, `caffeine_mg`, `is_zero_sugar`, "
            "`tag` (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special).\n\n"
            "**Image upload:** Attach a JPEG, PNG, or WebP file (max 5MB) as the `image` field. "
            "The image is uploaded to S3 under `monster-drinks/{slug}.{ext}` and the `image_url` is set automatically.\n\n"
            "**Slug generation:** A URL-friendly slug is auto-generated from `name` and `flavour`.\n\n"
            "**Example:**\n"
            "`POST /api/v1/admin/monsters/` with form fields `name=Monster Ultra` and `flavour=Paradise`"
        ),
    )
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

    @monster_drink_namespace.doc(
        description=(
            "Retrieve a single Monster drink by its database ID.\n\n"
            "Returns the full product record including nutritional info, product line tag, "
            "and the S3 image URL.\n\n"
            "**Returns 404** if no Monster drink exists with the given ID.\n\n"
            "**Example:**\n"
            "`GET /api/v1/admin/monsters/3`"
        ),
    )
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monster drink fetched.")
    @monster_drink_namespace.marshal_with(monster_drink_model)
    @jwt_required()
    def get(self, record_id: int):
        """Retrieve a Monster drink by its ID."""
        return MonsterDrinkRepository.get_by_id(MonsterDrink, record_id)

    @monster_drink_namespace.doc(
        description=(
            "Update an existing Monster drink entry.\n\n"
            "**Request format:** `multipart/form-data`. Only include the fields you want to change — "
            "omitted fields are left unchanged.\n\n"
            "**Image replacement:** If a new `image` file is attached, it replaces the existing S3 image. "
            "The old image is deleted after the new one is confirmed uploaded.\n\n"
            "**Slug update:** If `name` or `flavour` changes, the slug and S3 image key are updated accordingly.\n\n"
            "**Returns 404** if no Monster drink exists with the given ID.\n\n"
            "**Example:**\n"
            "`PUT /api/v1/admin/monsters/3` with form field `calories=160`"
        ),
    )
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

    @monster_drink_namespace.doc(
        description=(
            "Delete a Monster drink and its associated S3 image.\n\n"
            "The database record is removed first, then the S3 image is cleaned up. "
            "This also affects any store availability records referencing this monster.\n\n"
            "**Returns 404** if no Monster drink exists with the given ID.\n\n"
            "**Example:**\n"
            "`DELETE /api/v1/admin/monsters/3`"
        ),
    )
    @monster_drink_namespace.response(HttpStatus.OK.value, "Monster drink deleted.")
    @jwt_required()
    def delete(self, record_id: int):
        """Delete a Monster drink by its ID."""
        MonsterDrinkRepository.delete_with_image(record_id)
        return HttpResponseGenerator.generate_response(HttpStatus.OK)
