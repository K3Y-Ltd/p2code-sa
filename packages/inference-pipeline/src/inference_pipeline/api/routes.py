from flask import Blueprint

from .health_endpoint import vitals_endpoint
from .inference_endpoint import inference_endpoint

api = Blueprint("api", __name__)

api.register_blueprint(vitals_endpoint, url_prefix="/api")
api.register_blueprint(inference_endpoint)
