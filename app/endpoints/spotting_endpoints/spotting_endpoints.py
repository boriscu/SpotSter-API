from flask_restx import Resource, fields
from werkzeug.datastructures import FileStorage

from app.models.enums.http_status import HttpStatus
from app.models.pg.spotting_report import SpottingReport
from app.services.spotting_services.spotting_report_service import SpottingReportService

from . import spotting_namespace


spotting_upload_parser = spotting_namespace.parser()
spotting_upload_parser.add_argument(
    "file", location="files", type=FileStorage, required=True,
    help="Image file of the spotted Monster drink",
)
spotting_upload_parser.add_argument(
    "latitude", location="form", type=float, required=True,
    help="Latitude coordinate where the photo was taken",
)
spotting_upload_parser.add_argument(
    "longitude", location="form", type=float, required=True,
    help="Longitude coordinate where the photo was taken",
)

spotting_list_parser = spotting_namespace.parser()
spotting_list_parser.add_argument("limit", type=int, location="args", default=20, help="Max reports to return")
spotting_list_parser.add_argument("offset", type=int, location="args", default=0, help="Number of reports to skip")

spotting_report_model = spotting_namespace.model("SpottingReport", {
    "id": fields.Integer(description="Report ID"),
    "image_url": fields.String(description="S3 URL of the uploaded image"),
    "latitude": fields.Float(description="Latitude"),
    "longitude": fields.Float(description="Longitude"),
    "status": fields.String(description="Processing status: pending, matched, rejected"),
    "matched_monster_drink_id": fields.Integer(description="Matched monster drink ID", attribute="matched_monster_drink"),
    "matched_store_id": fields.Integer(description="Matched store ID", attribute="matched_store"),
    "rejection_reason": fields.String(description="Reason for rejection if applicable"),
    "created_at": fields.DateTime(),
})


@spotting_namespace.route("/", methods=["POST", "GET"])
class SpottingListEndpoint(Resource):
    """Endpoint for submitting and listing spotting reports."""

    @spotting_namespace.doc(
        description=(
            "Submit a photo of a Monster drink spotted in the wild.\n\n"
            "**Request format:** `multipart/form-data` with three fields:\n"
            "- `file` (required) — image file (JPEG, PNG, or WebP)\n"
            "- `latitude` (required) — latitude where the photo was taken\n"
            "- `longitude` (required) — longitude where the photo was taken\n\n"
            "**Processing pipeline:**\n"
            "1. Image is uploaded to S3\n"
            "2. Vision LLM identifies which Monster drink is in the photo\n"
            "3. Nearest store within 1km is matched to the coordinates\n"
            "4. If both match, the store's availability record is updated\n\n"
            "**Possible outcomes:**\n"
            "- `matched` — Monster identified and store found, availability updated\n"
            "- `rejected` — image is not a Monster drink, or no store nearby, or unknown variant\n\n"
            "No authentication required.\n\n"
            "**Example:**\n"
            "`POST /api/v1/public/spottings/` with `file=<image>`, `latitude=44.8125`, `longitude=20.4612`"
        ),
    )
    @spotting_namespace.expect(spotting_upload_parser)
    @spotting_namespace.response(HttpStatus.CREATED.value, "Spotting processed.")
    def post(self):
        """Upload an image with coordinates to report a Monster drink sighting."""
        args = spotting_upload_parser.parse_args()
        file = args["file"]
        latitude = args["latitude"]
        longitude = args["longitude"]

        if not file or not file.filename:
            return {"message": "No file provided"}, HttpStatus.BAD_REQUEST.value

        file_data = file.read()
        content_type = file.content_type or "image/jpeg"

        result = SpottingReportService.process_spotting(
            file_data=file_data,
            filename=file.filename,
            content_type=content_type,
            latitude=latitude,
            longitude=longitude,
        )

        return result, HttpStatus.CREATED.value

    @spotting_namespace.doc(
        description=(
            "List all spotting reports, newest first, with pagination.\n\n"
            "Returns a paginated list of spotting reports including image URLs, coordinates, "
            "processing status, and matched monster/store IDs.\n\n"
            "**Pagination:** Use `limit` (default 20) and `offset` (default 0) query parameters.\n\n"
            "**Response format:**\n"
            "```json\n"
            '{"reports": [...], "total": 42, "limit": 20, "offset": 0}\n'
            "```\n\n"
            "No authentication required.\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/spottings/?limit=10&offset=20`"
        ),
    )
    @spotting_namespace.expect(spotting_list_parser)
    @spotting_namespace.response(HttpStatus.OK.value, "Reports fetched.")
    def get(self):
        """Retrieve spotting reports with pagination."""
        args = spotting_list_parser.parse_args()
        limit = args.get("limit", 20)
        offset = args.get("offset", 0)

        query = SpottingReport.select().order_by(SpottingReport.created_at.desc())
        total = query.count()
        reports = list(query.offset(offset).limit(limit))

        return {
            "reports": [
                {
                    "id": report.id,
                    "image_url": report.image_url,
                    "latitude": report.latitude,
                    "longitude": report.longitude,
                    "status": report.status,
                    "matched_monster_drink_id": report.matched_monster_drink_id,
                    "matched_store_id": report.matched_store_id,
                    "rejection_reason": report.rejection_reason,
                    "created_at": str(report.created_at),
                }
                for report in reports
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@spotting_namespace.route("/<int:report_id>", methods=["GET"])
class SpottingDetailEndpoint(Resource):
    """Endpoint for retrieving a single spotting report."""

    @spotting_namespace.doc(
        description=(
            "Retrieve a single spotting report by its ID.\n\n"
            "Returns the full report including the uploaded image URL, coordinates, processing status "
            "(`pending`, `matched`, or `rejected`), matched monster/store IDs, and rejection reason if applicable.\n\n"
            "No authentication required.\n\n"
            "**Returns 404** if no report exists with the given ID.\n\n"
            "**Example:**\n"
            "`GET /api/v1/public/spottings/12`"
        ),
    )
    @spotting_namespace.response(HttpStatus.OK.value, "Report fetched.")
    @spotting_namespace.marshal_with(spotting_report_model)
    def get(self, report_id: int):
        """Retrieve a spotting report by its ID."""
        return SpottingReport.get_by_id(report_id)
