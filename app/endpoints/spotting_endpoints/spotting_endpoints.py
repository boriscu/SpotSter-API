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

    @spotting_namespace.doc(description="Submit a new Monster drink spotting report.")
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

    @spotting_namespace.doc(description="List all spotting reports.")
    @spotting_namespace.response(HttpStatus.OK.value, "Reports fetched.")
    @spotting_namespace.marshal_list_with(spotting_report_model)
    def get(self):
        """Retrieve all spotting reports."""
        return list(SpottingReport.select().order_by(SpottingReport.created_at.desc()))


@spotting_namespace.route("/<int:report_id>", methods=["GET"])
class SpottingDetailEndpoint(Resource):
    """Endpoint for retrieving a single spotting report."""

    @spotting_namespace.doc(description="Get a spotting report by ID.")
    @spotting_namespace.response(HttpStatus.OK.value, "Report fetched.")
    @spotting_namespace.marshal_with(spotting_report_model)
    def get(self, report_id: int):
        """Retrieve a spotting report by its ID."""
        return SpottingReport.get_by_id(report_id)
