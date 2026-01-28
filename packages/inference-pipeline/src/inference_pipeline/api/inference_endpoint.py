"""
This file has all HATEOAS endpoints for the inference pipeline.

The endpoints are:
- POST /attestation - Create an inference attestation
- GET /attestation - Get all inference attestation IDs
- GET /attestation/<int:attestation_id> - Get the result of an inference attestation
- GET /attestation/<int:attestation_id>/report - Get the STIX report of an inference attestation
- GET /attestation/<int:attestation_id>/status - Get the status of an inference attestation

The endpoints are used to interact with the inference pipeline to create and retrieve inference attestations.
"""

import os
import yaml

from flask import Blueprint, jsonify, request, g, current_app

from inference_pipeline.database import (
    InferenceRepository,
    get_session,
)

from inference_pipeline.utils import (
    compute_hash,
    docker_compose_parser,
    kubernetes_values_parser,
    make_image,
    run_inference,
)
from inference_pipeline.core import (
    create_container,
    export_container_to_tar,
    delete_dangling_containers_and_images,
)
from inference_pipeline.stix import build_stix_attestation_report

from ..logging import LOGGING_INFERENCE, fmt_msg

inference_endpoint = Blueprint("inference", __name__)


def generate_links(attestation_id: int):
    """
    Generate HATEOAS links for the inference attestation.

    Parameters
    ----------
    attestation_id : int
        The ID of the inference attestation result.

    Returns
    -------
    List
        A list of HATEOAS links for the inference attestation.
    """
    base_uri = f"/attestation/{attestation_id}"

    return [
        {"rel": "self", "href": base_uri, "method": "GET"},
        {"rel": "report", "href": f"{base_uri}/report", "method": "GET"},
        {"rel": "status", "href": f"{base_uri}/status", "method": "GET"},
    ]


def cleanup_files(extensions=("tar", "png")):
    """
    Cleanup PNG & TAR files after processing to free up space.
    """
    base_cwd = os.getcwd()

    check = lambda f: any(f.endswith(ext) for ext in extensions)

    for root, _, files in os.walk(base_cwd):
        for file in files:
            if check(file):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    current_app.logger.debug(f"Deleting file: {file_path}")
                except Exception as e:
                    current_app.logger.debug(f"Error deleting file {file_path}: {e}")


@inference_endpoint.route("/attestation/<int:attestation_id>", methods=["GET"])
def get_attestation_by_id(attestation_id: int):
    """
    Endpoint to get the result of an inference.

    Parameters
    ----------
    attestation_id : int
        The ID of the inference result

    Returns
    -------
    flask.Response
        JSON response with the inference result.
    """
    with get_session() as session:

        repo = InferenceRepository(session)
        result = repo.get_by_id(attestation_id)

        if not result:
            return jsonify(error="Attestation not found"), 404

        current_app.logger.info(
            f"Retrieved attestation with ID: {result.id} and sa_hash: {result.sa_hash}"
        )

        return jsonify(
            {
                "metadata": {
                    "id": result.id,
                    "created_at": result.created_at.isoformat(),
                    "application_area": result.application_area,
                    "status": result.status.value,
                    "links": generate_links(result.id),
                },
                "data": result.stix_report,
            }
        )


@inference_endpoint.route("/attestation", methods=["POST"])
def create_attestation():
    """
    Endpoint to get the result of an inference.

    Parameters
    ----------
    attestation_id : int
        The ID of the inference result

    Returns
    -------
    flask.Response
        JSON response with the inference result.
    """
    with get_session() as session:
        try:
            repository = InferenceRepository(session)

            current_app.logger.info(LOGGING_INFERENCE["log__receive_request"])

            current_app.logger.info(LOGGING_INFERENCE["log__parse_request"])

            # Get the Application Area from the request
            application_area = request.args.get("aa", type=int)
            if not application_area:
                return jsonify(error="Application Area not provided"), 400

            # Check the content-type of the request
            if request.content_type != "application/x-yaml":
                return (
                    jsonify({"error": "Content-Type must be application/x-yaml"}),
                    400,
                )

            # Parse the YAML content
            yaml_data = request.data.decode("utf-8").strip()
            current_app.logger.info(fmt_msg("1/5: YAML file received", level=1))
            current_app.logger.debug(f"{repr(yaml_data)}")

            if not yaml_data:
                return jsonify({"error": "No YAML file provided"}), 400

            # Convert the YAML data to a dictionary
            yaml_dict = yaml.safe_load(yaml_data)
            current_app.logger.info(fmt_msg("2/5: YAML file parsed", level=1))
            current_app.logger.info(fmt_msg(f"YAML Data: {yaml_dict}", level=2))

            # Compute the hash of the YAML data
            yaml_hash = compute_hash(yaml_data)
            current_app.logger.info(
                fmt_msg(f"3/5: YAML hash computed -> {yaml_hash}", level=1)
            )

            # Check if the yaml_hash is stored in the database
            current_app.logger.info(fmt_msg("4/5: Checking internal cache", level=1))
            result = repository.get_by_sa_hash(yaml_hash)

            if result:
                msg = f"5/5: ✓ Found existing attestation report with id: {result.id} and hash {result.sa_hash}"

                current_app.logger.info(fmt_msg(msg, level=1))
                return jsonify(
                    {
                        "metadata": {
                            "id": result.id,
                            "created_at": result.created_at.isoformat(),
                            "application_area": result.application_area,
                            "status": result.status.value,
                            "links": generate_links(result.id),
                        },
                        "data": result.stix_report,
                    }
                )
            else:
                msg = "5/5: ✗ No existing attestation report found. Continue to attestation"

                current_app.logger.info(fmt_msg(msg, level=1))

            current_app.logger.info(LOGGING_INFERENCE["log__init_sa_process"])

            # Check if the YAML is docker-compose or Kubernetes manifest
            if "services" not in yaml_dict:
                current_app.logger.info(
                    fmt_msg("1/2: Parsing kubernetes manifest", level=1)
                )
                containers_to_build = kubernetes_values_parser(yaml_dict)
            else:
                current_app.logger.info(
                    fmt_msg("1/2: Parsing `docker-compose` file", level=1)
                )
                containers_to_build = docker_compose_parser(yaml_dict)

            # Load the ML models
            models = g.models

            # Load the selected model based on the application area
            model = models[application_area]
            current_app.logger.info(
                fmt_msg(
                    f"2/2: Loading Machine Learning model for AA={application_area}",
                    level=1,
                )
            )

            container_images_meta = []

            # Check if the Docker client is available in the global context
            docker_client = g.docker_client

            # Add a service-based cache to skip duplicated services
            service_cache = {}

            current_app.logger.info(LOGGING_INFERENCE["log__init_sa_sequentially"])

            # Iterate over the services in the YAML file
            for container in containers_to_build:

                container_img_name = container["image"]
                container_img_tag = container["tag"]
                container_name = container["container_name"]

                current_app.logger.info(
                    fmt_msg(
                        LOGGING_INFERENCE["log__attest_service"].format(container_name),
                        level=1,
                    )
                )

                current_app.logger.info(
                    fmt_msg("Checking internal per-service cache.", level=2)
                )
                container_img_meta = service_cache.get(
                    (container_img_name, container_img_tag)
                )

                # If container image metadata are found in cache add to meta and continue
                if container_img_meta:
                    current_app.logger.info(
                        fmt_msg("✓: Found cached attestation result.", level=3)
                    )
                    container_images_meta.append(container_img_meta)
                    continue
                else:
                    current_app.logger.info(
                        fmt_msg(
                            "✗: No cached attestation result found. Continue with service attestation.",
                            level=3,
                        )
                    )

                current_app.logger.info(
                    fmt_msg(LOGGING_INFERENCE["log__create_container"], level=2)
                )

                # Create container with the extracted image
                container_to_assess = create_container(
                    client=docker_client,
                    container_image_name=container_img_name,
                    container_image_tag=container_img_tag,
                    container_name=container_name,
                )

                current_app.logger.info(
                    fmt_msg(LOGGING_INFERENCE["log__export_container"], level=2)
                )

                # Export the container to a tar file
                tar_path = export_container_to_tar(
                    container=container_to_assess, tar_name=container_name
                )
                if not tar_path:
                    current_app.logger.error(
                        f"✗: Failed to export container {container_to_assess}"
                    )
                    continue

                # Convert the tar file to an image
                current_app.logger.info(
                    fmt_msg(LOGGING_INFERENCE["log__create_image"], level=2)
                )

                image_path = make_image(tar_path=tar_path)
                current_app.logger.info(
                    fmt_msg(f"✓: RGB image created: {image_path}", level=3)
                )

                # Run inference on the image
                current_app.logger.info(
                    fmt_msg(LOGGING_INFERENCE["log__infer"], level=2)
                )
                response = run_inference(image_path, model)

                # Register container metadata
                container_img_meta = {
                    "name": container["image"],
                    "tag": container["tag"],
                    "path_to_tar": tar_path,
                    "hash": container_to_assess.image.id,
                    "classification": response,
                }

                # store to cache
                current_app.logger.info(
                    fmt_msg(LOGGING_INFERENCE["log__parse_response"], level=2)
                )
                service_cache[(container_img_name, container_img_tag)] = (
                    container_img_meta
                )

                container_images_meta.append(container_img_meta)

                # Prune the containers and images
                current_app.logger.info(
                    fmt_msg(LOGGING_INFERENCE["log__clear_docker"], level=2)
                )

                delete_dangling_containers_and_images(docker_client)

                # Delete `tar` file to free up space
                os.remove(tar_path)

            # Creating final attestation report
            current_app.logger.info(LOGGING_INFERENCE["log__create_attestation_report"])
            stix_attestation_report = build_stix_attestation_report(
                container_images_meta=container_images_meta
            )
            current_app.logger.info(
                fmt_msg(f"STIX Attestation Report: {stix_attestation_report}", level=1)
            )

            # Remove PNG & TAR files
            cleanup_files()

            current_app.logger.info(LOGGING_INFERENCE["log__cache_response"])

            result = repository.create_record(
                sa_hash=yaml_hash,
                stix_report=stix_attestation_report,
                application_area=application_area,
            )
            if not result:
                return jsonify(error="Attestation not store"), 404

            current_app.logger.info(
                fmt_msg(
                    f"✓: Stored attestation with ID: {result.id} and sa_hash: {result.sa_hash}",
                    level=1,
                )
            )

            return jsonify(
                {
                    "metadata": {
                        "id": result.id,
                        "created_at": result.created_at.isoformat(),
                        "application_area": result.application_area,
                        "status": result.status.value,
                        "links": generate_links(result.id),
                    },
                    "data": result.stix_report,
                }
            )
        except yaml.YAMLError as e:
            delete_dangling_containers_and_images(docker_client)
            return jsonify({"error": "Invalid YAML data."}), 400
        except Exception as e:
            delete_dangling_containers_and_images(docker_client)
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@inference_endpoint.route("/attestation/<int:attestation_id>/report", methods=["GET"])
def get_report_by_id(attestation_id: int):
    """
    Endpoint to get the STIX report of an attestation result.

    Parameters
    ----------
    attestation_id : int
        The ID of the attestation result.

    Returns
    -------
    flask.Response
        JSON response with the STIX report.
    """
    with get_session() as session:

        repo = InferenceRepository(session)
        result = repo.get_by_id(attestation_id)

        if not result:
            return jsonify(error="Attestation not found"), 404

        return jsonify({"data": result.stix_report})


@inference_endpoint.route("/attestation/<int:attestation_id>/status", methods=["GET"])
def get_status_by_id(attestation_id: int):
    """
    Endpoint to get the status of an attestation result.

    Parameters
    ----------
    attestation_id : int
        The ID of the attestation result.

    Returns
    -------
    flask.Response
        JSON response with the status of the attestation result.
    """
    with get_session() as session:
        repo = InferenceRepository(session)
        result = repo.get_by_id(attestation_id)
        if not result:
            return jsonify(error="Attestation not found"), 404

        return jsonify({"status": result.status.value})


@inference_endpoint.route("/attestation", methods=["GET"])
def get_all_attestations():
    """
    Endpoint to get all the attestation results stored in the database.

    Returns
    -------
    flask.Response
        JSON response with all IDs of attestation results.
    """
    with get_session() as session:
        repo = InferenceRepository(session)
        results = repo.get_all()
        if not results:
            return jsonify(error="No attestations found"), 404

        payload = {
            "metadata": {"total": len(results)},
            "data": [
                {
                    "id": result.id,
                    "created_at": result.created_at.isoformat(),
                    "application_area": result.application_area,
                    "status": result.status.value,
                }
                for result in results
            ],
        }
        return jsonify(payload), 200
