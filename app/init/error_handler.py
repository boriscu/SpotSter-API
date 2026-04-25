from flask import Flask
from flask_restx import Api
from peewee import DoesNotExist, IntegrityError, PeeweeException
from werkzeug.exceptions import HTTPException
import sentry_sdk

from jwt.exceptions import ExpiredSignatureError
from flask_jwt_extended.exceptions import NoAuthorizationError

from app.models.enums.http_status import HttpStatus
from app.helpers.http_response_generator import HttpResponseGenerator
from app.init.logger_setup import LoggerSetup


def register_error_handlers(app: Flask, api: Api) -> None:
    """
    Registers error handlers for HTTP status codes, ORM exceptions,
    JWT exceptions, and generic exceptions.

    Args:
        app: The Flask application instance.
        api: The flask-restx API instance.
    """

    logger = LoggerSetup.get_logger("errors")

    def generate_error_handler(status: HttpStatus):
        """
        Generates a Flask error handler for a specific HTTP status.

        Args:
            status: The HTTP status for which to generate the handler.

        Returns:
            Callable: A Flask error handler function.
        """

        def handler(error):
            log_message = f"Error {status.value}: {str(error)}, Type: {type(error).__name__}"
            logger.error(log_message)

            if status.value >= 500:
                sentry_sdk.capture_exception(error)
                sentry_sdk.capture_message(log_message, level="error")
            elif status.value >= 400:
                sentry_sdk.capture_message(
                    f"Client error {status.value}: {str(error)}", level="warning"
                )

            return HttpResponseGenerator.generate_error_response(status)

        return handler

    for status in HttpStatus:
        if 400 <= status.value < 600:
            app.register_error_handler(status.value, generate_error_handler(status))

    @api.errorhandler(DoesNotExist)
    def handle_does_not_exist(error):
        """Handle Peewee DoesNotExist exceptions."""
        logger.warning(f"DoesNotExist: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.NOT_FOUND)

    @api.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        """Handle Peewee IntegrityError exceptions."""
        logger.error(f"IntegrityError: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.BAD_REQUEST)

    @api.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError exceptions."""
        logger.error(f"ValueError: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.BAD_REQUEST)

    @api.errorhandler(PeeweeException)
    def handle_peewee_exception(error):
        """Handle general Peewee exceptions."""
        logger.error(f"PeeweeException: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.BAD_REQUEST)

    @api.errorhandler(PermissionError)
    def handle_permission_exception(error):
        """Handle PermissionError exceptions."""
        logger.warning(f"PermissionError: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.FORBIDDEN)

    @api.errorhandler(RuntimeError)
    def handle_runtime_exception(error):
        """Handle RuntimeError exceptions."""
        logger.error(f"RuntimeError: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(
            HttpStatus.INTERNAL_SERVER_ERROR
        )

    @api.errorhandler(KeyError)
    def handle_key_exception(error):
        """Handle KeyError exceptions."""
        logger.error(f"KeyError: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.BAD_REQUEST)

    @api.errorhandler(TypeError)
    def handle_type_exception(error):
        """Handle TypeError exceptions."""
        logger.error(f"TypeError: {error}")
        sentry_sdk.capture_message(str(error))
        return HttpResponseGenerator.generate_error_response(HttpStatus.BAD_REQUEST)

    @api.errorhandler(ExpiredSignatureError)
    def handle_expired_signature(error):
        """Handle expired JWT token errors."""
        logger.warning(f"ExpiredSignatureError: {error}")
        return HttpResponseGenerator.generate_error_response(HttpStatus.UNAUTHORIZED)

    @api.errorhandler(NoAuthorizationError)
    def handle_no_auth(error):
        """Handle missing or invalid JWT errors."""
        logger.warning(f"NoAuthorizationError: {error}")
        return HttpResponseGenerator.generate_error_response(HttpStatus.FORBIDDEN)

    @api.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle exceptions raised by abort."""
        status_code = error.code if hasattr(error, "code") and error.code else 500
        logger.error(f"HTTPException {status_code}: {error}")
        return HttpResponseGenerator.generate_error_response(HttpStatus(status_code))

    @api.errorhandler(Exception)
    def handle_general_exception(error):
        """
        Handle general exceptions not specifically mapped to an HTTP status.
        Defaults to INTERNAL_SERVER_ERROR.
        """
        logger.error(f"Unhandled Exception: {type(error).__name__}: {error}")
        sentry_sdk.capture_exception(error)
        return HttpResponseGenerator.generate_error_response(
            HttpStatus.INTERNAL_SERVER_ERROR
        )
