import click
from flask.cli import with_appcontext

from app.init.logger_setup import LoggerSetup
from app.init.db_init import router


from app.models.pg.admin_user import AdminUser
from app.models.pg.monster_drink import MonsterDrink
from app.models.pg.store import Store
from app.models.pg.store_monster_availability import StoreMonsterAvailability
from app.models.pg.spotting_report import SpottingReport

@click.command("create-migration")
@click.argument("name")
@with_appcontext
def command(name: str):
    """Create a new automatic migration script."""
    logger = LoggerSetup.get_logger("migrations")
    logger.info(f"Creating migration: {name}")

    try:
        router.create(
            name, 
            auto=[
                AdminUser, 
                MonsterDrink, 
                Store, 
                StoreMonsterAvailability, 
                SpottingReport
            ]
        )
        click.echo(f"Successfully created migration '{name}'.")
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        click.echo(f"Failed to create migration '{name}'. Error: {e}")
