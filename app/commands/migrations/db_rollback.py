import click
from flask.cli import with_appcontext

from app.init.logger_setup import LoggerSetup
from app.init.db_init import router


@click.command("db-rollback")
@with_appcontext
def command():
    """Rollback the last migration."""
    logger = LoggerSetup.get_logger("migrations")
    logger.info("Rolling back the last migration")

    try:
        router.rollback()
        click.echo("Rollback successful.")
    except Exception as e:
        logger.error(f"Error executing rollback: {e}")
        click.echo(f"Failed to perform rollback. Error: {e}")
