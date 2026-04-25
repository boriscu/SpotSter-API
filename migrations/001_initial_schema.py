"""Peewee migrations -- 001_initial_schema.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress
from decimal import ROUND_HALF_EVEN

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    @migrator.create_model
    class AdminUser(pw.Model):
        id = pw.AutoField()
        created_at = pw.DateTimeField()
        updated_at = pw.DateTimeField()
        email = pw.TextField(unique=True)
        password = pw.TextField()
        is_admin = pw.BooleanField(default=True)
        is_active = pw.BooleanField(default=True)

        class Meta:
            table_name = "admin_user"

    @migrator.create_model
    class MonsterDrink(pw.Model):
        id = pw.AutoField()
        created_at = pw.DateTimeField()
        updated_at = pw.DateTimeField()
        name = pw.CharField(max_length=100, unique=True)
        flavour = pw.CharField(max_length=100, unique=True)
        slug = pw.CharField(max_length=100, unique=True)
        description = pw.TextField(null=True)
        calories = pw.IntegerField(null=True)
        sugar_grams = pw.DecimalField(auto_round=False, decimal_places=1, max_digits=10, null=True, rounding=ROUND_HALF_EVEN)
        caffeine_mg = pw.IntegerField(null=True)
        is_zero_sugar = pw.BooleanField(default=False)
        image_url = pw.TextField(null=True)

        class Meta:
            table_name = "monster_drink"

    @migrator.create_model
    class Store(pw.Model):
        id = pw.AutoField()
        created_at = pw.DateTimeField()
        updated_at = pw.DateTimeField()
        name = pw.CharField(max_length=200)
        address = pw.TextField(null=True)
        latitude = pw.DoubleField()
        longitude = pw.DoubleField()

        class Meta:
            table_name = "store"

    @migrator.create_model
    class SpottingReport(pw.Model):
        id = pw.AutoField()
        created_at = pw.DateTimeField()
        updated_at = pw.DateTimeField()
        image_url = pw.TextField()
        latitude = pw.DoubleField()
        longitude = pw.DoubleField()
        status = pw.CharField(default='pending', max_length=20)
        matched_monster_drink = pw.ForeignKeyField(column_name='matched_monster_drink_id', field='id', model=migrator.orm['monster_drink'], null=True, on_delete='SET NULL')
        matched_store = pw.ForeignKeyField(column_name='matched_store_id', field='id', model=migrator.orm['store'], null=True, on_delete='SET NULL')
        rejection_reason = pw.TextField(null=True)

        class Meta:
            table_name = "spotting_report"

    @migrator.create_model
    class StoreMonsterAvailability(pw.Model):
        id = pw.AutoField()
        created_at = pw.DateTimeField()
        updated_at = pw.DateTimeField()
        store = pw.ForeignKeyField(column_name='store_id', field='id', model=migrator.orm['store'], on_delete='CASCADE')
        monster_drink = pw.ForeignKeyField(column_name='monster_drink_id', field='id', model=migrator.orm['monster_drink'], on_delete='CASCADE')

        class Meta:
            table_name = "store_monster_availability"
            indexes = [(('store', 'monster_drink'), True)]


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.remove_model('store_monster_availability')

    migrator.remove_model('spotting_report')

    migrator.remove_model('store')

    migrator.remove_model('monster_drink')

    migrator.remove_model('admin_user')
