"""
This is a helper script for downloading locally the COSOCO dataset
that holds RGB images representing benign and malware compromised
software containers. The script uses the python API of HuggingFace
Hub. 
"""

from huggingface_hub import snapshot_download

import argparse


def parse_args():
    """
    Arguments for the `download_cosoco_data.py` script.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--subfolder",
        action="store",
        type=str,
        default="1024-unrolled",
        choices=["1024-unrolled", "2048-unrolled", "4096-unrolled_n"],
        help="COSOCO dataset subfolder to download data from.",
    )

    parser.add_argument(
        "--local_dir",
        action="store",
        type=str,
        default="/home/anousias/p2code/datasets/",
        help="COSOCO dataset subfolder to download data from.",
    )

    args = parser.parse_args()

    return args


def main():
    """
    Download locally COSOCO dataset from HuggingFace.
    """
    args = parse_args()

    REPO_ID = "k3ylabs/cosoco-image-dataset"

    subfolder = args.subfolder
    local_dir = args.local_dir

    allow_patterns = "{}/*.*".format(subfolder)

    snapshot_download(
        repo_id=REPO_ID,
        allow_patterns=allow_patterns,
        repo_type="dataset",
        local_dir=local_dir,
    )


if __name__ == "__main__":
    main()
