import os
import toml
import argparse

import cv2
import torch
from pyasn1_modules.rfc5990 import camellia128_Wrap

from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from container_classification.utils import (
    validate_device,
)

from container_classification.models import (
    AlexNet,
    ResNet18,
)

MODELS = {
    "alexnet": AlexNet,
    "resnet18": ResNet18,
}


def parse_args():
    """
    Parse arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cfg_path", type=str, help="Path to configuration `.toml` file."
    )

    args = parser.parse_args()

    return args


def load_model(model_type, model_path, device):
    """
    Load explanation model.
    """
    device = validate_device(device)

    model_cls = MODELS[model_type]

    model = model_cls().to(device)

    model_weights = torch.load(model_path, map_location=device)["state"]
    model.load_state_dict(model_weights)

    if model_type == "alexnet":
        features_layers = list(model.pretrained_model.features.children())
        target_layers = [features_layers[12]]

    elif model_type == "resnet18":
        features_layers = list(model.named_children())
        target_layers = [features_layers[0][1].maxpool]

    return model, target_layers


def load_image(image_path: str, flipped: bool = False) -> torch.FloatTensor:
    """
    Load image to explain.
    """
    img = cv2.imread(image_path)

    if flipped:
        img = cv2.flip(img, 0)

    return torch.FloatTensor(img).permute(2, 0, 1).unsqueeze(0)


def main():
    """
    Predict  a model explanation
    """
    args = parse_args()

    with open(args.cfg_path, "r") as f:
        cfg = toml.load(f)

    image_path = os.path.join(cfg["image"]["path"], cfg["image"]["name"])

    # print("Loading image & model...")
    # img = load_image(image_path=image_path, flipped=cfg["image"]["flipped"])

    model, target_layers = load_model(
        model_type=cfg["model"]["type"],
        model_path=cfg["model"]["path"],
        device=cfg["model"]["device"],
    )
    cam = GradCAM(model=model, target_layers=target_layers)


    from container_classification.dataset.iterable_dataset import extract_patches_from_image_infer

    patches = extract_patches_from_image_infer(image_path, patch_size=(256, 256))
    targets = [ClassifierOutputTarget(cfg["gradcam"]["class_to_xai"])]

    print("Explaining instance...")
    dictator = {}
    for (img_name, patch_id, patch) in patches:

        grayscale_cam = cam(input_tensor=patch.unsqueeze(0), targets=targets)[0, :] * 255.0
        dictator["patch_id"] = [grayscale_cam, cam.outputs]

        print("Saving explanation...")
        save_name = "cam-{}-{}-{}--class:{}.png".format(cfg["model"]["type"], cfg["image"]["name"], patch_id, cam.outputs.argmax())
        save_path = os.path.join(cfg["output"]["path"], save_name)
        cv2.imwrite(save_path, grayscale_cam)

    # cv2.imwrite(save_path, grayscale_cam)
    # print(f"Image class prediction: {model_outputs.argmax()}")


if __name__ == "__main__":
    main()
