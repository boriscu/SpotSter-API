from flask_restx import Namespace

auth_namespace = Namespace("Auth", description="Admin authentication endpoints")

from .auth_endpoints import *
