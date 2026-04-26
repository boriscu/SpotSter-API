from datetime import datetime

from flask_restx import Resource

from app.models.enums.http_status import HttpStatus
from app.models.enums.monster_tag import MonsterTag
from app.models.pg.monster_drink import MonsterDrink
from app.services.store_services.store_repository import StoreRepository

from . import public_store_namespace


stores_parser = public_store_namespace.parser()
stores_parser.add_argument("sw_lat", type=float, location="args", help="Southwest corner latitude of visible map area")
stores_parser.add_argument("sw_lng", type=float, location="args", help="Southwest corner longitude of visible map area")
stores_parser.add_argument("ne_lat", type=float, location="args", help="Northeast corner latitude of visible map area")
stores_parser.add_argument("ne_lng", type=float, location="args", help="Northeast corner longitude of visible map area")
stores_parser.add_argument("lat", type=float, location="args", help="Map center latitude (used for distance sorting within viewport)")
stores_parser.add_argument("lng", type=float, location="args", help="Map center longitude (used for distance sorting within viewport)")
stores_parser.add_argument("limit", type=int, location="args", default=50, help="Max stores to return")
stores_parser.add_argument("offset", type=int, location="args", default=0, help="Number of stores to skip (for pagination)")
stores_parser.add_argument("search", type=str, location="args", help="Search by store name or monster name/flavour")
stores_parser.add_argument("flavours", type=str, location="args", help="Comma-separated monster slugs to filter by")
stores_parser.add_argument("tags", type=str, location="args", help="Comma-separated tag values (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special)")
stores_parser.add_argument("spotted_since", type=str, location="args", help="ISO date string (e.g. 2026-04-01)")


@public_store_namespace.route("/", methods=["GET"])
class PublicStoreListEndpoint(Resource):
    """Public endpoint for browsing stores with filtering, search, and pagination."""

    @public_store_namespace.doc(
        description=(
            "Returns stores within the visible map area, with optional filtering and pagination.\n\n"
            "**Bounding box (viewport):**\n"
            "Pass `sw_lat`, `sw_lng`, `ne_lat`, `ne_lng` to scope results to the visible map rectangle. "
            "Handles anti-meridian wrapping (where sw_lng > ne_lng). "
            "If omitted, all stores are returned.\n\n"
            "**Distance sorting:**\n"
            "Pass `lat` and `lng` (map center) to sort results by distance from that point. "
            "If omitted, results are sorted by store name.\n\n"
            "**Filters:**\n"
            "- `search` — matches store name OR monster name/flavour (case-insensitive)\n"
            "- `tags` — comma-separated MonsterTag values (1=Original, 2=Ultra, 3=Java, 4=Juiced, 5=Special)\n"
            "- `flavours` — comma-separated monster slugs\n"
            "- `spotted_since` — ISO date, only stores with spottings after this date\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/stores/?sw_lat=44.7&sw_lng=20.3&ne_lat=44.9&ne_lng=20.6&lat=44.8&lng=20.45&limit=50`"
        ),
    )
    @public_store_namespace.expect(stores_parser)
    @public_store_namespace.response(HttpStatus.OK.value, "Stores fetched.")
    def get(self):
        """Retrieve stores within viewport bounds, with search, filters, and pagination."""
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
            sw_lat=args.get("sw_lat"),
            sw_lng=args.get("sw_lng"),
            ne_lat=args.get("ne_lat"),
            ne_lng=args.get("ne_lng"),
            center_lat=args.get("lat"),
            center_lng=args.get("lng"),
            limit=args.get("limit", 50),
            offset=args.get("offset", 0),
            search=args.get("search"),
            flavour_slugs=flavour_slugs,
            tags=tags,
            spotted_since=spotted_since,
        )


@public_store_namespace.route("/<int:store_id>", methods=["GET"])
class PublicStoreDetailEndpoint(Resource):
    """Public endpoint for viewing a store with full detail."""

    @public_store_namespace.doc(
        description=(
            "Retrieve full detail for a single store.\n\n"
            "Returns the store's location info along with:\n"
            "- **available_monsters** — all Monster drinks spotted at this store, sorted by most recently spotted\n"
            "- **recent_spottings** — the last 10 spotting report images with matched monster info\n"
            "- **flavour_count** — number of distinct Monster flavours available\n"
            "- **total_spottings** — lifetime count of spotting reports at this store\n\n"
            "No authentication required.\n\n"
            "**Returns 404** if no store exists with the given ID.\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/stores/5`"
        ),
    )
    @public_store_namespace.response(HttpStatus.OK.value, "Store fetched.")
    def get(self, store_id: int):
        """Retrieve full store detail (public, no auth required)."""
        return StoreRepository.get_store_detail(store_id)


@public_store_namespace.route("/filters", methods=["GET"])
class PublicFiltersEndpoint(Resource):
    """Public endpoint returning available filter options for store browsing."""

    @public_store_namespace.doc(
        description=(
            "Returns available filter options for the store browsing UI.\n\n"
            "Currently returns **tags** — the product line categories (Original, Ultra, Java, Juiced, Special) "
            "that have at least one Monster drink in the database, along with the count of monsters in each tag.\n\n"
            "Use this to populate filter chips or dropdowns in the client. Tags with zero monsters are excluded.\n\n"
            "No authentication required.\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/stores/filters`"
        ),
    )
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
