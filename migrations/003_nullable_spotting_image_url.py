"""Peewee migrations -- 003_nullable_spotting_image_url.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Allow image_url to be null on spotting_report (rejected spottings have no S3 upload)."""

    migrator.sql('ALTER TABLE spotting_report ALTER COLUMN image_url DROP NOT NULL')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Revert image_url back to non-nullable."""

    migrator.sql('ALTER TABLE spotting_report ALTER COLUMN image_url SET NOT NULL')
