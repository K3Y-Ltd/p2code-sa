from typing import Dict

import os
import time
import logging
import docker

from docker.models.containers import Container
from inference_pipeline.logging import fmt_msg

logger = logging.getLogger("inference_pipeline.api.app")


def initialize_docker_client(
    login_to_remote: bool = False, login_kw: Dict = {}, delay: int = 3
) -> docker.DockerClient:
    """
    Create a Docker client to interact with the Docker daemon, with retry logic.

    Parameters
    ----------
    use_remote : bool
        A boolean whether to use a remote registry for the docker client.
    login_kw : Dict
        A dictionary with keyword arguments for the `docker.DockerClient.login`
        method. Expected keys are ('registry', 'username', 'password').
    delay : int
        Number of seconds to delay between login retries.

    Returns
    -------
    docker.DockerClient
        The Docker client to interact with the Docker daemon in a global context.
    """
    docker_client = None
    retries = 0

    registry = login_kw.get("registry")
    username = login_kw.get("username")
    password = login_kw.get("password")

    while docker_client is None and retries < 20:

        try:
            logger.info(fmt_msg("1/2: Initializing Docker client", level=1))
            client = docker.from_env()
            logger.info(fmt_msg("✓: Client initialized", level=1))
            logger.info(fmt_msg("2/2: Connecting to registry", level=1))

            # Login to registry using credentials
            if login_to_remote is True:
                client.login(username=username, password=password, registry=registry)

            logger.info(
                fmt_msg("✓: Client initialized and connected to registry", level=1)
            )
            return client

        except Exception as e:
            retries += 1
            logger.error(
                fmt_msg(
                    f"✗: Failed connecting to registry: attempt {retries}): {e}",
                    level=1,
                )
            )
            logger.info(fmt_msg(f"Retrying in {delay} seconds...", level=1))
            time.sleep(delay)


def create_container(
    client: docker.client.DockerClient,
    container_image_name: str,
    container_image_tag: str,
    container_name: str,
) -> Container:
    """
    Create a container from the given image.

    Parameters
    ----------
    client : docker.client.DockerClient
        The Docker client to create the container.
    container_image_name : str
        The name of the container image.
    container_image_tag : str
        The tag of the container image.
    container_name : str
        The name of the container.

    Returns
    -------
    Container
        The created container.
    """
    try:
        # Pull the image from the provided registry
        logger.info(
            fmt_msg(
                f"1/2: Pulling dockerized image: {container_image_name}:{container_image_tag}",
                level=3,
            )
        )
        image = client.images.pull(container_image_name, tag=container_image_tag)

        logger.info(
            fmt_msg(
                f"✓: Pulled dockerized image: {container_image_name}:{container_image_tag}",
                level=3,
            )
        )

        # Create a container from the image
        logger.info(
            fmt_msg(
                f"2/2: Creating container from image: {container_image_name}:{container_image_tag}",
                level=3,
            )
        )

        container = client.containers.create(
            image, command="sh", name=container_name, detach=True
        )

        logger.info(
            fmt_msg(
                f"✓: Created container: {container_name}",
                level=3,
            )
        )

        return container
    except docker.errors.APIError as e:
        logger.error(fmt_msg(f"✗: Error during docker creation: {e}", level=3))
        return None


def export_container_to_tar(container: Container, tar_name: str) -> str:
    """
    Export the container to a tar file.

    Parameters
    ----------
    container : Container
        The container to export.
    tar_name : str
        The name of the tar file.

    Returns
    -------
    str
        The path to the exported tar file.
    """
    tar_name = "{}.tar".format(str(tar_name))
    tar_path = os.path.join(os.getcwd(), tar_name)

    logger.info(fmt_msg(f"Exporting container {container} to {tar_path}", level=3))
    try:
        tar_file = container.export()
        with open(tar_path, "wb") as tar:
            for chunk in tar_file:
                tar.write(chunk)

        logger.info(
            fmt_msg(
                f"✓: Container {container} exported at TAR file '{tar_name}'", level=3
            )
        )
        return tar_path

    except Exception as e:
        logger.error(
            fmt_msg(
                f"✗: Error exporting TAR for container {container} with error: {e}",
                level=3,
            )
        )
        return None


def delete_dangling_containers_and_images(client: docker.client.DockerClient) -> None:
    """
    Delete all dangling images and containers.

    Parameters
    ----------
    client : docker.client.DockerClient
        The Docker client to delete the dangling containers and images.

    Returns
    -------
    None
        Removes dangling images and containers.
    """
    try:
        # Delete all dangling containers
        logger.info(fmt_msg("1/2: Deleting dangling containers", level=3))
        client.containers.prune()
        logger.info(fmt_msg("✓: Successfully deleted dangling containers", level=3))

        # Delete all dangling images
        logger.info(fmt_msg("2/2: Deleting dangling images", level=3))
        client.images.prune()
        logger.info(fmt_msg("✓: Successfully deleted dangling images", level=3))
        return
    except Exception as e:
        logger.error(
            fmt_msg(f"✗: Error deleting dangling containers and images: {e}", level=3)
        )
        return None
