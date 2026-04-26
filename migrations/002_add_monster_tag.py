"""Peewee migrations -- 002_add_monster_tag.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Add tag column to monster_drink table."""

    migrator.add_fields(
        'monster_drink',
        tag=pw.IntegerField(null=True),
    )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Remove tag column from monster_drink table."""

    migrator.remove_fields('monster_drink', 'tag')
