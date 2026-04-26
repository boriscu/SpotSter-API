from flask import Flask
from flask_restx import Api

from app.endpoints.auth_endpoints import auth_namespace
from app.endpoints.monster_drink_endpoints import monster_drink_namespace
from app.endpoints.store_endpoints import store_namespace
from app.endpoints.public_monster_endpoints import public_monster_namespace
from app.endpoints.public_store_endpoints import public_store_namespace
from app.endpoints.spotting_endpoints import spotting_namespace

from app.init.error_handler import register_error_handlers


def init_app_routes(app: Flask) -> None:
    """
    Initialize all API routes and register namespaces.

    Args:
        app: The Flask application instance.
    """
    authorizations = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token",
        },
    }

    api = Api(
        app,
        version="1.0",
        title="SpotSter API Documentation",
        description="API documentation for the SpotSter Monster Drink Spotting application.",
        authorizations=authorizations,
        security="Bearer Auth",
        prefix="/api",
    )

    # Admin endpoints
    api.add_namespace(auth_namespace, path="/v1/auth")
    api.add_namespace(monster_drink_namespace, path="/v1/admin/monsters")
    api.add_namespace(store_namespace, path="/v1/admin/stores")

    # Public endpoints
    api.add_namespace(public_monster_namespace, path="/v1/public/monsters")
    api.add_namespace(public_store_namespace, path="/v1/public/stores")
    api.add_namespace(spotting_namespace, path="/v1/public/spottings")

    register_error_handlers(app, api)
