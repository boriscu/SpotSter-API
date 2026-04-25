from flask import Flask
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
import sentry_sdk


def register_before_handlers(app: Flask) -> None:
    """
    Registers before_request handlers for all HTTP requests.
    Sets the Sentry user context from the JWT token when available.

    Args:
        app: The Flask application instance.
    """

    @app.before_request
    def before_request_func():
        try:
            verify_jwt_in_request()
            jwt_data = get_jwt()
            if jwt_data:
                sentry_sdk.set_user({"id": get_jwt_identity()})
        except Exception:
            pass
