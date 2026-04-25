from flask_restx import Namespace

monster_drink_namespace = Namespace("Admin Monsters", description="Admin CRUD operations for Monster drinks")

from .monster_drink_endpoints import *
