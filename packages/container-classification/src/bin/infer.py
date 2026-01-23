import argparse

from container_classification.infer import load_model, infer
from container_classification.infer import initialize_data_loader_infer
from container_classification.utils import validate_device


def parse_arguments():
    """
    Command line arguments for the `classification/bin/evaluate` script.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Build a dataset of instances representing instructions for "
            "creating a diverse set of docker containers. The instructions "
            "include cases where both 'clean' and 'infected' containers will "
            "be created."
        )
    )

    parser.add_argument(
        "--model_path",
        action="store",
        type=str,
        help="Path to model to be used for inference.",
    )

    parser.add_argument(
        "--model_type",
        action="store",
        type=str,
        default="alexnet",
        help="Type of the inference model.",
    )

    parser.add_argument(
        "--image_path",
        action="store",
        type=str,
        default="./data/",
        help="Path to image representing a container to apply the container-classifier.",
    )

    parser.add_argument(
        "--device",
        action="store",
        type=str,
        default="cpu",
        help="Device to use for model prediction.",
    )

    args = parser.parse_args()

    return args


def main():
    """
    Main functionality.
    """
    args = parse_arguments()

    model_path = args.model_path
    model_type = args.model_type
    image_path = args.image_path
    patch_size = [256, 256]

    # Configure device
    device = validate_device(args.device)

    model = load_model(model_path, model_type)

    data_loader = initialize_data_loader_infer(image_path, patch_size)

    res = infer(model=model, data_loader=data_loader, device=device.type)

    print(res)


if __name__ == "__main__":
    main()
