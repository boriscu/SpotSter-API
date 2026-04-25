from flask_restx import Namespace

spotting_namespace = Namespace("Spottings", description="Monster drink spotting report endpoints")

from .spotting_endpoints import *
