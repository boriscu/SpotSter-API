from flask_restx import Namespace

store_namespace = Namespace("Admin Stores", description="Admin CRUD operations for stores")

from .store_endpoints import *
