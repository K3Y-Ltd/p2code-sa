from typing import Dict, Any

import os
import uuid

from logging.config import dictConfig
from flask import Flask, jsonify, request, g

from inference_pipeline.core import initialize_docker_client
from inference_pipeline.database import init_database, create_session_factory
from inference_pipeline.utils import validate_model_paths

from inference_pipeline.api.health_endpoint import vitals_endpoint
from inference_pipeline.api.inference_endpoint import inference_endpoint

from inference_pipeline.logging import LOGGING_APP
from inference_pipeline.logging import get_default_logging_config, fmt_msg

from container_classification.infer import load_model


def set_logger_config(config: Dict | None = None) -> None:
    """
    Set logger configuration.
    """
    if config is None:
        config = get_default_logging_config()

    dictConfig(config)


def app_load_models(model_paths, model_type, logger):
    """
    Load application ml models.
    """
    models = {}

    for key, path in model_paths.items():
        models[key] = load_model(path, model_type)

        logger.info(fmt_msg(f"Model {key} loaded from {path} successfully", level=1))

    logger.info(
        fmt_msg(
            "✓: In total, {} models loaded successfully".format(len(models)), level=1
        )
    )

    return models


def create_flask_app(config: Dict[str, Any]) -> Flask:
    """
    Create a Flask app with the given configuration.

    Parameters
    ----------
    config : Dict[str, Any]
        The configuration yaml file.

    Returns
    -------
    Flask
        A `Flask` app instance.
    """
    # setup logging
    set_logger_config(config["logging"])

    # Initialize Flask app
    app = Flask(__name__)
    app.config.update(config["flask"])

    # disable werkzeug for a more clear logging
    # _logger = logging.getLogger("werkzeug")    # _logger.disabled = True

    app.logger.info(LOGGING_APP["log__app_init"])

    # Initialize docker client
    app.logger.info(LOGGING_APP["log__docker_init"])
    
    login_to_remote = config.get("docker", {}).get("login_to_remote", False)
    login_kw = {
        "registry": os.getenv("CONTAINER_REGISTRY", default="ghcr.io"),
        "username": os.getenv("CONTAINER_REGISTRY_USERNAME"),
        "password": os.getenv("CONTAINER_REGISTRY_TOKEN"),
    }

    docker_client = initialize_docker_client(
        login_to_remote=login_to_remote, login_kw=login_kw
    )

    # Validate ML model paths
    app.logger.info(LOGGING_APP["log__models_validate"])
    
    # NOTE: Fixed used model_type `resnet18` 
    model_paths = validate_model_paths(config)
    model_type = "resnet18"

    # Load ML models
    app.logger.info(LOGGING_APP["log__models_load"])

    models = app_load_models(
        model_paths=model_paths, model_type=model_type, logger=app.logger
    )

    # Initialize the database connection
    app.logger.info(LOGGING_APP["log__db_init"])

    engine = init_database(config["database"]["uri"])
    create_session_factory(engine)

    # Request context logging
    @app.before_request
    def log_request_start():
        """
        Log request start.
        """
        request_id = str(uuid.uuid4())

        g.request_id = request_id
        g.docker_client = docker_client
        g.logger = app.logger
        g.models = models

        app.logger.info(
            f"--> {request.method} | {request.path} (Request ID: {request_id})"
        )

    @app.after_request
    def log_request_end(response):
        """
        Log request end.
        """
        app.logger.info(
            f"<-- {request.method} | {request.path} (Request ID: {g.request_id})"
        )
        return response

    @app.errorhandler(404)
    def handle_404(e):
        """
        Return error 404.
        """
        return jsonify(error=str(e)), 404

    @app.errorhandler(500)
    def handle_500(e):
        """
        Return error 500.
        """
        app.logger.info(f"Server error: {str(e)}")
        return jsonify(error="Internal server error"), 500

    app.logger.info(LOGGING_APP["log__reg_endpoints"])
    app.register_blueprint(vitals_endpoint, url_prefix="/api")
    app.register_blueprint(inference_endpoint)
    app.logger.info(fmt_msg("✓: Endpoints registered successfully", level=1))

    app.logger.info("✓: Software attestation service initialized successfully")

    return app
