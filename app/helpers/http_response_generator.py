from flask import Response

from app.models.maps.http_status_message_map import http_status_message_map

from app.models.enums.http_status import HttpStatus


class HttpResponseGenerator:
    """
    Generates standardised JSON HTTP responses for success and error cases.
    All endpoint responses should be created through this class for consistency.
    """

    @staticmethod
    def generate_response(status: HttpStatus) -> Response:
        """
        Generates a JSON response with a message corresponding to a given HTTP status code.

        Args:
            status: An enum value of HttpStatus representing the HTTP status code.

        Returns:
            Response: A Flask Response object containing the JSON-formatted message and the HTTP status code.
        """

        message = http_status_message_map.get(status, "An unknown error occurred")
        return Response(
            f'{{"message": "{message}"}}',
            status=status.value,
            mimetype="application/json",
        )

    @staticmethod
    def generate_error_response(status: HttpStatus) -> Response:
        """
        Generates a JSON error response with a message corresponding to a given HTTP status code.

        Args:
            status: An enum value of HttpStatus representing the HTTP status code.

        Returns:
            Response: A tuple of (response dict, status code).
        """

        message = http_status_message_map.get(status, "An unknown error occurred")
        response_content = {
            "message": message,
            "error": {"message": message, "status_code": status.value},
        }

        response = response_content, status.value
        return response
