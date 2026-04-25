import click
from flask.cli import with_appcontext

from config.app_config import AppConfig
from app.models.pg.admin_user import AdminUser
from app.services.admin_auth_services.admin_auth_service import AdminAuthService


@click.command("seed-admin")
@with_appcontext
def seed_admin_command():
    """
    Seeds an initial admin user from environment variables.
    Checks if the user already exists to prevent duplicates.
    """
    email = AppConfig.ADMIN_EMAIL
    password = AppConfig.ADMIN_PASSWORD

    if not email or not password:
        click.echo("ADMIN_EMAIL or ADMIN_PASSWORD missing from config. ❌")
        return

    try:
        AdminUser.get(AdminUser.email == email)
        click.echo(f"Admin user {email} already exists. ✅")
    except AdminUser.DoesNotExist:
        hashed_password = AdminAuthService.hash_password(password)
        AdminUser.create(email=email, password=hashed_password)
        click.echo(f"Admin user {email} created successfully! ✅")
