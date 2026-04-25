import click
from flask.cli import with_appcontext

from app.init.db_init import router


@click.command("db-migrate-status")
@with_appcontext
def command():
    """Show the status of migrations (applied vs unapplied)."""
    try:
        done = router.done
        diff = router.diff

        click.echo("\nApplied Migrations:")
        for m in done:
            click.echo(f"  - {m}")

        click.echo("\nPending Migrations:")
        for m in diff:
            click.echo(f"  - {m}")
        
        click.echo("")
    except Exception as e:
        click.echo(f"Failed to get migration status. Error: {e}")
