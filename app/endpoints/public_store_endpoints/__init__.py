from flask_restx import Namespace

public_store_namespace = Namespace("Public Stores", description="Public store browsing, filtering, and detail endpoints")

from .public_store_endpoints import *
