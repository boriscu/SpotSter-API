from datetime import datetime

from flask_restx import Resource

from app.models.enums.http_status import HttpStatus
from app.models.enums.monster_tag import MonsterTag
from app.models.pg.monster_drink import MonsterDrink
from app.services.store_services.store_repository import StoreRepository

from . import public_store_namespace


stores_parser = public_store_namespace.parser()
stores_parser.add_argument("lat", type=float, location="args", help="User latitude")
stores_parser.add_argument("lng", type=float, location="args", help="User longitude")
stores_parser.add_argument("limit", type=int, location="args", default=20, help="Max stores to return")
stores_parser.add_argument("offset", type=int, location="args", default=0, help="Number of stores to skip (for pagination)")
stores_parser.add_argument("search", type=str, location="args", help="Search by store name or monster name/flavour")
stores_parser.add_argument("flavours", type=str, location="args", help="Comma-separated monster slugs to filter by")
stores_parser.add_argument("tags", type=str, location="args", help="Comma-separated tag values (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special)")
stores_parser.add_argument("spotted_since", type=str, location="args", help="ISO date string (e.g. 2026-04-01)")


@public_store_namespace.route("/", methods=["GET"])
class PublicStoreListEndpoint(Resource):
    """Public endpoint for browsing stores with filtering, search, and pagination."""

    @public_store_namespace.doc(description="List stores with optional filters. If lat/lng provided, sorted by distance.")
    @public_store_namespace.expect(stores_parser)
    @public_store_namespace.response(HttpStatus.OK.value, "Stores fetched.")
    def get(self):
        """Retrieve stores with available monsters, supporting search, filters, and pagination."""
        args = stores_parser.parse_args()

        flavour_slugs = None
        if args.get("flavours"):
            flavour_slugs = [s.strip() for s in args["flavours"].split(",") if s.strip()]

        tags = None
        if args.get("tags"):
            tags = [int(t.strip()) for t in args["tags"].split(",") if t.strip()]

        spotted_since = None
        if args.get("spotted_since"):
            spotted_since = datetime.fromisoformat(args["spotted_since"])

        return StoreRepository.get_stores(
            latitude=args.get("lat"),
            longitude=args.get("lng"),
            limit=args.get("limit", 20),
            offset=args.get("offset", 0),
            search=args.get("search"),
            flavour_slugs=flavour_slugs,
            tags=tags,
            spotted_since=spotted_since,
        )


@public_store_namespace.route("/<int:store_id>", methods=["GET"])
class PublicStoreDetailEndpoint(Resource):
    """Public endpoint for viewing a store with full detail."""

    @public_store_namespace.doc(description="Get a store with available monsters, recent spottings, and counts.")
    @public_store_namespace.response(HttpStatus.OK.value, "Store fetched.")
    def get(self, store_id: int):
        """Retrieve full store detail (public, no auth required)."""
        return StoreRepository.get_store_detail(store_id)


@public_store_namespace.route("/filters", methods=["GET"])
class PublicFiltersEndpoint(Resource):
    """Public endpoint returning available filter options for store browsing."""

    @public_store_namespace.doc(description="Get available filter options (tags with monster counts).")
    @public_store_namespace.response(HttpStatus.OK.value, "Filters fetched.")
    def get(self):
        """Retrieve available tags and their monster counts for filter UI."""
        monsters = list(MonsterDrink.select(MonsterDrink.tag))

        tag_counts = {}
        for monster in monsters:
            if monster.tag is not None:
                tag_counts[monster.tag] = tag_counts.get(monster.tag, 0) + 1

        return {
            "tags": [
                {
                    "value": tag.value,
                    "label": tag.name.capitalize(),
                    "count": tag_counts.get(tag.value, 0),
                }
                for tag in MonsterTag
                if tag.value in tag_counts
            ],
        }
