from flask import make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Resource, fields

from app.models.enums.http_status import HttpStatus
from app.helpers.http_response_generator import HttpResponseGenerator
from app.services.admin_auth_services.admin_auth_service import AdminAuthService

from . import auth_namespace


login_request_model = auth_namespace.model("LoginRequest", {
    "email": fields.String(required=True, description="Admin email address"),
    "password": fields.String(required=True, description="Admin password"),
})

login_response_model = auth_namespace.model("LoginResponse", {
    "msg": fields.String(description="Status message"),
    "access_token": fields.String(description="JWT access token"),
})


@auth_namespace.route("/", methods=["POST", "GET"])
class AuthEndpoint(Resource):
    """Admin authentication endpoint for login and token validation."""

    @auth_namespace.doc(description="Log in using an email and password.")
    @auth_namespace.expect(login_request_model, validate=True)
    @auth_namespace.response(HttpStatus.OK.value, "Login Successful", model=login_response_model)
    @auth_namespace.response(HttpStatus.UNAUTHORIZED.value, "Unauthorized")
    def post(self):
        """Authenticate an admin user and return an access token."""
        access_token = AdminAuthService.login(request.get_json())
        if access_token:
            return make_response(
                {
                    "msg": "Login successful",
                    "access_token": access_token,
                },
                HttpStatus.OK.value,
            )
        else:
            return {"msg": "Password is incorrect"}, HttpStatus.UNAUTHORIZED.value

    @auth_namespace.doc(description="Check the validity of the current user's JWT token.")
    @auth_namespace.response(HttpStatus.OK.value, "Token is valid")
    @auth_namespace.response(HttpStatus.UNAUTHORIZED.value, "Unauthorized")
    @jwt_required()
    def get(self):
        """Validate the current JWT token."""
        get_jwt_identity()
        return HttpResponseGenerator.generate_response(HttpStatus.OK)
