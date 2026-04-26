from flask_restx import Namespace

public_monster_namespace = Namespace("Public Monsters", description="Public read-only endpoints for Monster drinks")

from .public_monster_endpoints import *
