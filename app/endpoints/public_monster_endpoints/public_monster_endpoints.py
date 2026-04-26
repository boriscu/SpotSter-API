from flask_restx import Resource, fields

from app.models.enums.http_status import HttpStatus
from app.models.pg.monster_drink import MonsterDrink

from . import public_monster_namespace


monster_public_model = public_monster_namespace.model("MonsterDrinkPublic", {
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
    "tag": fields.Integer(description="Product line tag"),
})


@public_monster_namespace.route("/", methods=["GET"])
class PublicMonsterListEndpoint(Resource):
    """Public endpoint for browsing the Monster drink catalogue."""

    @public_monster_namespace.doc(
        description=(
            "Returns the full Monster drink catalogue.\n\n"
            "Lists every Monster drink in the database with product details, nutritional info, "
            "product line tag, and image URL. No authentication required.\n\n"
            "Use this to populate filter dropdowns, search suggestions, or a browsable catalogue in the app.\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/monsters/`"
        ),
    )
    @public_monster_namespace.response(HttpStatus.OK.value, "Monsters fetched.")
    @public_monster_namespace.marshal_list_with(monster_public_model)
    def get(self):
        """Retrieve all Monster drink entries (public, no auth required)."""
        return list(MonsterDrink.select())


@public_monster_namespace.route("/<int:monster_id>", methods=["GET"])
class PublicMonsterDetailEndpoint(Resource):
    """Public endpoint for viewing a single Monster drink."""

    @public_monster_namespace.doc(
        description=(
            "Retrieve a single Monster drink by its ID.\n\n"
            "Returns the full product record including nutritional details, product line tag, "
            "and the ground truth image URL. No authentication required.\n\n"
            "**Returns 404** if no Monster drink exists with the given ID.\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/monsters/3`"
        ),
    )
    @public_monster_namespace.response(HttpStatus.OK.value, "Monster drink fetched.")
    @public_monster_namespace.marshal_with(monster_public_model)
    def get(self, monster_id: int):
        """Retrieve a Monster drink by its ID (public, no auth required)."""
        return MonsterDrink.get_by_id(monster_id)
