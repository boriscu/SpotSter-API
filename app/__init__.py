import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app import routes

from config.app_config import AppConfig

from app.commands import register_commands

from app.init.before_handler import register_before_handlers
from app.init.sentry_init import SentryInitializer

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)


def create_app() -> Flask:
    """
    Application factory that creates and configures the Flask application.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)

    app.app_context().push()

    AppConfig.load_config()

    SentryInitializer.initialize()

    app.config.from_object(AppConfig)

    CORS(
        app,
        resources={r"/api/v1/*": {"origins": AppConfig.ALLOWED_ORIGINS}},
    )

    JWTManager(app)

    routes.init_app_routes(app)

    register_commands(app)
    register_before_handlers(app)

    return app
