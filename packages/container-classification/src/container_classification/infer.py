from typing import Tuple, List

import cv2
import torch
import numpy as np

from torch.utils.data import DataLoader

from container_classification.models import (
    AlexNet,
    ResNet18,
    MobileNetV2,
    SqueezeNet,
    VGG11,
    ShuffleNet,
    EfficientNet,
)

from container_classification.dataset.iterable_dataset import (
    ImagePatchIterableDatasetInfer,
    build_dp_from_iterable_dataset_infer,
)


def initialize_data_loader_infer(
    paths: str | List[str], patch_size: List[int]
) -> DataLoader:
    """
    Initialize DataLoader for an inference iterable dataset.
    """
    data = build_dp_from_iterable_dataset_infer(
        ImagePatchIterableDatasetInfer(paths=paths, patch_size=patch_size)
    )

    return DataLoader(
        data, batch_size=64, drop_last=False, num_workers=1, shuffle=False
    )


def load_img(path_to_img: str) -> np.ndarray:
    """
    Load image from path to np.ndarray.
    """
    img = cv2.imread(path_to_img)

    return img


def _parse_result_for_incode_sa(y_preds, y_probs):
    """
    Parse results for incode software attestation
    """
    LABELS = ["benign", "malevolent"]

    for img_name, pred in y_preds.items():

        label = LABELS[pred]

        prob = y_probs[img_name]

        break

    return {"class": label, "probability": prob}


def get_predictions_from_threshold_probabilities(
    probs: torch.Tensor, t: float = 0.75
) -> torch.Tensor:
    """
    Threshold prediction probabilities.

    Parameters
    ----------
    probs : torch.Tensor
        A tensor of shape `(n, 2)` corresponding to probabilities for two classes:
        {0: 'benign', 1: 'malevolent'}. The probabilities are independent and do
        not sum up to one.

    Returns
    -------
    preds : torch.Tensor
        A tensor of shape `(n, 1)` corresponding to class predictions per patch.
    """
    MALEVOLENT_IDX = 1

    return (probs[:, MALEVOLENT_IDX] > t).long()


def infer(
    model: torch.nn.Module, data_loader: DataLoader, device: str = "cpu"
) -> np.ndarray:
    """
    Classify single image record of dockerized container.

    This method loads input image, splits it into patches and classifies
    them, and aggregating the results.

    Parameters
    ----------
    model : torch.nn.Module
        A loaded model.
    loader : DataLoader
        A torch DataLoader to load samples for inference,
    """
    model.eval()

    y_preds, y_probs = {}, {}

    for img_names, patch_ids, img in data_loader:

        img = img.to(device=device)

        # estimate logits on batch
        _logits = model.forward(img)

        # get probabilities and final prediction
        _probs = torch.sigmoid(_logits)

        # get predictions by thresholding probabilities
        _preds = get_predictions_from_threshold_probabilities(_probs, t=0.75)

        # Accuracy per image
        for img_name, patch_id, pred, prob in zip(
            img_names, patch_ids, _preds.tolist(), _probs.tolist()
        ):

            if img_name not in y_preds:
                y_preds[img_name] = {patch_id.item(): pred}
            else:
                y_preds[img_name].update({patch_id.item(): pred})

            if img_name not in y_probs:
                y_probs[img_name] = {patch_id.item(): prob[pred]}
            else:
                y_probs[img_name].update({patch_id.item(): prob[pred]})

    y_preds_agg, y_probs_agg = {}, {}

    for img_name, patch_preds in y_preds.items():

        img_pred = max(patch_preds.values())

        if img_pred == 1:
            img_prob = max(
                [
                    y_probs[img_name][patch_id]
                    for patch_id, pred in y_preds[img_name].items()
                    if pred == 1
                ]
            )

        elif img_pred == 0:
            img_prob = sum(y_probs[img_name].values()) / len(y_probs[img_name])

        y_preds_agg[img_name] = img_pred
        y_probs_agg[img_name] = img_prob

    return _parse_result_for_incode_sa(y_preds_agg, y_probs_agg)


def load_model(
    model_path: str, model_type: str, device: str = "cpu"
) -> torch.nn.Module:
    """
    Load model from `pt` file.
    """
    MODELS = {
        "alexnet": AlexNet,
        "resnet18": ResNet18,
        "mobile_net": MobileNetV2,
        "squeeze_net": SqueezeNet,
        "vgg": VGG11,
        "efficient_net": EfficientNet,
        "shuffle_net": ShuffleNet,
    }

    state_dict = torch.load(model_path, map_location=device)["state"]

    model = MODELS[model_type]().to(device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    return model
