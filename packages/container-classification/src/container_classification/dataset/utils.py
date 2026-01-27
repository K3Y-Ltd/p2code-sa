from typing import Tuple, List

import os
import glob
import json

import numpy as np


def _from_json(json_path: str, data_dir: str) -> Tuple[List[str], List[int]]:
    """
    Initialize `ImageDataset` instance from `.json` file.

    The JSON file should include a list of records where each record
    has the following schema:
    ```
    [
        {
            "name": "benign-8b34-CNTA00001-0",
            "label": "benign"
        },
    ]
    ```

    Parameters
    ----------
    json_path : str
        Path to the json file where the dataset is defined.
    data_dir : str
        Path to the folder that holds dataset images.

    Returns
    -------
    Tuple[List[str], List[int]]
        A tuple of lists with image paths and image labels.
    """
    with open(json_path, "r") as f:
        records = json.load(f)

    paths = [os.path.join(data_dir, record["name"] + ".png") for record in records]
    labels = [0 if record["label"] == "benign" else 1 for record in records]

    return paths, labels


def _from_dir(data_dir: str) -> Tuple[List[str], List[int]]:
    """
    Initialize `ImageDataset` instance from path to rood diretory.

    NOTE: This function selects all files from a folder without distinguishing
    between images or not. The image label is inferred from the image name.

    Parameters
    ----------
    data_dir : str
        Path to the folder that holds dataset images.

    Returns
    -------
    Tuple[List[str], List[int]]
        A tuple of lists with image paths and image labels.
    """
    paths = glob.glob(os.path.join(data_dir, "*", "*"))

    labels = [0 if "benign" in path else 1 for path in paths]

    return paths, labels


def _get_mask_path(file_path: str) -> str:
    """
    Get mask path from file_path.
    """
    filename, _ = os.path.splitext(file_path)

    return "{}.mask.png".format(filename)


def _get_file_name(file_path: str) -> str:
    """
    Get file name from file_path.
    """
    # Get path tail part and remove `.png` suffix
    _, filename = os.path.split(file_path)
    filename, _ = os.path.splitext(filename)

    return filename


def one_hot_np(labels, num_classes=2):
    """
    Convert array of labels to one-hot vectors.
    """
    labels = np.array(labels, dtype="int32")

    return np.squeeze(np.eye(num_classes, dtype="float32")[labels])
