from typing import Tuple

from flask import Blueprint, jsonify
from flask import Response

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from inference_pipeline.database import get_session


vitals_endpoint = Blueprint("healthcheck", __name__)


@vitals_endpoint.route("/healthz", methods=["GET"])
def liveness_probe() -> Tuple[Response, int]:
    """
    Liveness probe endpoint: Checks if the application process is running

    Returns
    -------
    Tuple[Response, int]
        JSON response with status
    """
    return jsonify({"status": "alive"}), 200


@vitals_endpoint.route("/ready", methods=["GET"])
def readiness_probe() -> Tuple[Response, int]:
    """
    Readiness probe endpoint: Checks if service is ready to handle traffic.
    This includes checking the database connection.

    Returns
    -------
    Tuple[Response, int]
        JSON response with service readiness status
    """
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return jsonify({"status": "ready"}), 200
    except SQLAlchemyError as e:
        return jsonify({"status": "unavailable", "error": str(e)}), 503


@vitals_endpoint.route("/db", methods=["GET"])
def database_status() -> Tuple[Response, int]:
    """
    Checks if the database is running.

    Returns
    -------
    Tuple[Response, int]
        JSON response with status
    """
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return jsonify({"status": "database is running"}), 200
    except SQLAlchemyError as e:
        return jsonify({"status": "database is down", "error": str(e)}), 503
