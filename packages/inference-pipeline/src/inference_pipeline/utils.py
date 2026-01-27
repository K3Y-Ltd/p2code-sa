from typing import List, Dict, Any

import os
import hashlib
import logging

from .logging import fmt_msg

from binvis.binvis_iter import visualize_binary_iter
from container_classification.infer import infer, initialize_data_loader_infer

logger = logging.getLogger("inference_pipeline.api.app")


def docker_compose_parser(yaml_data: Dict) -> List[Dict]:
    """
    Parse the docker-compose file

    Parameters
    -----------
    yaml_data : Dict
        The yaml file parsed as a dictionary.

    Returns
    -------
    list
        A list of dictionaries containing the container name, image and tag:
        ```
        [
            {'container_name': 'influxdb', 'image': 'influxdb', 'tag': 'latest'},
            {'container_name': 'chronograf', 'image': 'chronograf', 'tag': 'latest'},
            {'container_name': 'grafana', 'image': 'grafana/grafana', 'tag': 'latest'}
        ]
        ```
    """

    containers = []

    for service_name, service_details in yaml_data["services"].items():
        image = service_details["image"]
        image, tag = image.split(":") if ":" in image else (image, None)
        if not tag:
            tag = "latest"

        container = {
            "container_name": service_name,
            "image": image,
            "tag": tag,
        }
        containers.append(container)

    return containers


def kubernetes_values_parser(yaml_data: Dict) -> List[Dict]:
    """
    Parse the kubernetes values file

    Parameters
    ----------
    yaml_data : Dict
        The `yaml` file representing a `values.yaml` file, part of a Helm Chart.

    Returns
    -------
    containers : List[Dict]
        A list of dictionaries with the container `container_name`, `image` and `tag`.

        ```
        [
            {'container_name': 'minio', 'image': 'quay.io/minio/minio', 'tag': 'latest'},
            {'container_name': 'mongo', 'image': 'mongo', 'tag': 'latest'},
        ]
        ```
    """

    containers = []

    for service_name, service_details in yaml_data.items():

        if "image" in service_details:

            img = service_details["image"]

            if isinstance(img, dict):

                if "repository" in img and "tag" in img:
                    container = {
                        "container_name": service_name,
                        "image": service_details["image"]["repository"],
                        "tag": service_details["image"]["tag"],
                    }

                else:
                    container = None

            elif isinstance(img, str):

                repo, tag = img.split(":") if ":" in img else (img, None)

                if tag is not None:
                    container = {
                        "container_name": service_name,
                        "image": repo,
                        "tag": tag,
                    }
                else:
                    container = None

            if container is None:
                continue
        else:
            continue

        containers.append(container)

    return containers


def compute_hash(data: str) -> str:
    """
    Compute the hash of a container_to_attest object. For example:

    {'container_name': 'influxdb', 'image': 'influxdb', 'tag': 'latest'}
    => 'd1b0e5d9f7e7a7e0a7b3c7f3f3f3f3f3'

    Parameters
    ----------
    data : str
        The data to hash.

    Returns
    -------
    str
        The hash of the data.
    """
    return hashlib.md5(data.encode()).hexdigest()


def make_image(
    tar_path: str,
) -> Dict:
    """
    Convert the tar file to an image.

    Parameters
    ----------
    tar_path : str
        The path to the tar file.

    Returns
    -------
    Dict
        The image and the path to the image.
    """
    # NOTE: The argument `step=30` makes sure that the input image
    # irrespectively of its input size will have a similar sampling
    # ratio with the one used on images during training. This argument
    # is model / training regime dependent.
    image = visualize_binary_iter(
        path=tar_path,
        layout_map="hilbert",
        layout_type="unrolled",
        color_block=None,
        show_progress=True,
        color_map=["class", "magnitude", "structure"],
        chunk_size=512 * 512,
        size=1024,
        step=30,
    )

    image_path = tar_path.replace(".tar", ".png")
    image.save(image_path, format="png")

    return image_path


def run_inference(image_path: str, model):
    """
    Run inference on the image.

    Parameters
    ----------
    image_path : str
        The path to the image.
    model
        The model to use for inference.

    Returns
    -------
    Dict
        The classification results.
    """
    patch_size = [256, 256]

    logger.info(fmt_msg(f"1/3: Initializing data loader", level=3))

    data_loader = initialize_data_loader_infer(image_path, patch_size)

    logger.info(fmt_msg(f"2/3: Perform attestation with ML model", level=3))
    res = infer(model=model, data_loader=data_loader, device="cpu")

    if isinstance(res, dict):
        for key, value in res.items():
            if not isinstance(
                value, (int, float, str)
            ):  # Check if value is not a native type
                res[key] = float(value)  # Coerce to float or appropriate type

    logger.info(fmt_msg(f"3/3: Receive attestation results: {res}", level=3))
    return res


def validate_model_paths(config: Dict[str, Any]) -> Dict:
    """
    Validate models' paths.

    Parameters
    ----------
    config : Dict
        The application input configuration.

    Returns
    -------
    Dict
        The verified model paths.
    """
    if "models" not in config:
        logger.error(f"✗: Model directory not found: {model_dir}")

        raise ValueError("Input configuration file does not specify models.")

    model_dir = config["models"]["path"]
    model_files = config["models"]["files"]

    # Validate path to models' directory
    if not os.path.exists(model_dir):
        logger.error(f"✗: Model directory not found: {model_dir}")

        raise FileNotFoundError(f"Model directory not found: {model_dir}")

    if not os.path.isdir(model_dir):
        logger.error("✗: Given model directory is not a directory")

        raise NotADirectoryError("Given model directory is not a directory")

    model_paths = {
        idx + 1: os.path.join(model_dir, model_file)
        for idx, model_file in enumerate(model_files)
    }

    for path in model_paths.values():

        if not os.path.exists(path):
            logger.error(f"✗: Model file not found in path: {path}")
            raise FileNotFoundError(f"Model file not found in path: {path}")

    logger.info(fmt_msg("✓: Model paths validated", level=1))

    return model_paths
