import click
from flask.cli import with_appcontext

from app.init.db_init import db


@click.command("db-health-check")
@with_appcontext
def db_health_check_command():
    """
    Checks if the database is ready to accept connections.
    Used during startup to wait for the DB container to be fully initialized.
    """
    try:
        db.connect()
        db.close()
        click.echo("Database is ready! ✅")
        import sys
        sys.exit(0)
    except Exception as e:
        click.echo(f"Database not ready: {str(e)} ❌")
        import sys
        sys.exit(1)
