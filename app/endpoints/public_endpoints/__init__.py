from flask_restx import Namespace

public_namespace = Namespace("Public", description="Public read-only endpoints for monsters and stores")

from .public_endpoints import *
