from typing import Dict

import os
import sys
import yaml
import argparse

from inference_pipeline.api import create_flask_app


def parse_args():
    """
    Command line arguments for the `inference-pipeline/bin/inference_api.py` script.
    """
    parser = argparse.ArgumentParser(description=("Execute the inference api script."))

    parser.add_argument(
        "--cfg_path",
        action="store",
        type=str,
        default="./config.yaml",
        help="Path to a `.yml` configuration file for the `inference-api.py` script.",
    )

    args = parser.parse_args()

    return args


def load_config(cfg_path: str | None = None) -> Dict:
    """
    Load the configuration file.

    Returns
    -------
    Dict
        The parsed configuration file as a dictionary.
    """
    if cfg_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(script_dir, "config.yaml")

    try:
        with open(cfg_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        sys.stderr.write(f"Error: Config file not found at {cfg_path}\n")
        sys.exit(1)
    except yaml.YAMLError as e:
        sys.stderr.write(f"Error: Invalid YAML in config file: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error loading config: {e}\n")
        sys.exit(1)


def main():
    """ """
    args = parse_args()

    config = load_config(cfg_path=args.cfg_path)

    app = create_flask_app(config)

    app.run(**config["flask"])


if __name__ == "__main__":
    main()
