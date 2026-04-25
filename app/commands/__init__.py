from flask import Flask

from app.commands.db_health_check import db_health_check_command

from app.commands.seeding.seed_admin_command import seed_admin_command

from app.commands.migrations.create_migration import command as create_migration_command
from app.commands.migrations.db_migrate import command as db_migrate_command
from app.commands.migrations.db_rollback import command as db_rollback_command
from app.commands.migrations.db_migrate_status import (
    command as db_migrate_status_command,
)


def register_commands(app: Flask) -> None:
    """
    Register all CLI commands with the Flask application.

    Args:
        app: The Flask application instance.
    """
    app.cli.add_command(db_health_check_command)

    app.cli.add_command(seed_admin_command)

    app.cli.add_command(create_migration_command)
    app.cli.add_command(db_migrate_command)
    app.cli.add_command(db_rollback_command)
    app.cli.add_command(db_migrate_status_command)
