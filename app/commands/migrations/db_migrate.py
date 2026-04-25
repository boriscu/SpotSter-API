import click
from flask.cli import with_appcontext

from app.init.logger_setup import LoggerSetup
from app.init.db_init import router


@click.command("db-migrate")
@with_appcontext
def command():
    """Run pending migrations."""
    logger = LoggerSetup.get_logger("migrations")
    logger.info("Running migrations")

    try:
        router.run()
        click.echo("Migrations applied successfully.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        click.echo(f"Failed to apply migrations. Error: {e}")
