from typing import Dict, Optional
from flask import abort
from flask_jwt_extended import create_access_token, get_jwt, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

from config.app_config import AppConfig

from app.models.enums.http_status import HttpStatus
from app.models.pg.admin_user import AdminUser


class AdminAuthService:
    """
    Service class for admin user authentication.
    Handles login, token management, and admin verification.
    """

    @staticmethod
    def login(data: Dict[str, str]) -> Optional[str]:
        """
        Logs in an admin user by validating the email and password.

        Args:
            data: A dictionary containing the user's email and password.

        Returns:
            Optional[str]: Access token if credentials are valid, None otherwise.
        """
        email = data.get("email")
        password = data.get("password")

        admin_user = AdminUser.get(AdminUser.email == email)

        if check_password_hash(admin_user.password, password):
            access_token = create_access_token(
                identity=str(admin_user.id),
                expires_delta=timedelta(minutes=int(AppConfig.TOKEN_EXPIRATION_TIME)),
                additional_claims={
                    "is_admin": admin_user.is_admin,
                    "is_active": admin_user.is_active,
                },
            )

            return access_token
        else:
            return None

    @staticmethod
    def check_if_admin() -> bool:
        """
        Checks if the current user is an admin based on the JWT token.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        try:
            verify_jwt_in_request()
            is_admin = bool(get_jwt().get("is_admin"))
        except Exception:
            is_admin = False

        return is_admin

    @staticmethod
    def check_if_admin_and_raise() -> None:
        """
        Validates if the current user token has admin privileges.

        Raises:
            HTTPException: A 403 Forbidden status if the user is not an admin.
        """
        if not AdminAuthService.check_if_admin():
            abort(HttpStatus.FORBIDDEN.value)

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Generates a secure hash of the provided password.

        Args:
            password: The plaintext password to hash.

        Returns:
            str: The hashed password string.
        """
        return generate_password_hash(password)
