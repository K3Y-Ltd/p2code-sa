from typing import Dict

import os
import sys
import toml
import argparse
import torch
import csv
import webdataset as wds

from torch.utils.data import DataLoader, IterableDataset

from container_classification.dataset import (
    ImageDataset,
    ImagePatchIterableDataset,
)

try:
    import wandb
except ImportError:
    print("`wandb` was not found. `wandb` functionalities will be disabled.")

from container_classification.dataset.iterable_dataset import (
    build_dp_from_iterable_dataset_infer,
    build_dp_from_webdataset_valid,
    build_wds_pipeline_data_from_shards,
)

from container_classification.utils import (
    validate_epoch,
    validate_device,
)

from container_classification.infer import load_model

from container_classification.models import (
    AlexNet,
    ResNet18,
    MobileNetV2,
    SqueezeNet,
    VGG11,
    ShuffleNet,
    EfficientNet,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cfg_path",
        type=str,
        help="Path to training configuration `.toml` file.",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="./runs/results/",
        help="Path to directory to store model.",
    )

    args = parser.parse_args()

    return args


def _initialize_iterable_dataset_json(cfg: Dict) -> Dict[str, IterableDataset]:
    """
    Initialize an iterable dataset with `.json` files.
    """
    kw = cfg["dataset"]["kw"]

    data_path = cfg["dataset"]["path"]

    data = {
        split: build_dp_from_iterable_dataset_infer(
            ImagePatchIterableDataset.from_json(path, data_path, **kw)
        )
        for split, path in cfg["dataset"]["json"].items()
    }

    return data


def _initialize_iterable_dataset_dir(cfg: Dict) -> Dict[str, IterableDataset]:
    """
    Initialize an iterable dataset given `dir`.
    """
    kw = cfg["dataset"]["kw"]

    data = {
        "test": build_dp_from_iterable_dataset_infer(
            ImagePatchIterableDataset.from_dir(cfg["dataset"]["dir"]["test"], **kw)
        )
    }

    return data


def _initialize_iterable_dataset_webdataset_single(
    cfg: Dict,
) -> Dict[str, IterableDataset]:
    """
    Initialize an iterable dataset with `.webd` files.
    """
    kw = cfg["dataset"]["kw"]

    data_path = cfg["dataset"]["path"]

    splits = cfg["dataset"]["splits"]

    data = {
        split: build_wds_pipeline_data_from_shards(data_path, split, **kw)
        for split in splits
    }

    return data


def initialize_iterable_datasets(cfg):
    """
    Initialize Iterable Dataset.
    """
    _DATASET_INITIALIZERS = {
        "json": _initialize_iterable_dataset_json,
        "dir": _initialize_iterable_dataset_dir,
        "webdataset": _initialize_iterable_dataset_webdataset_single,
    }

    fmt = cfg["dataset"]["format"]

    data = _DATASET_INITIALIZERS[fmt](cfg)

    if fmt in ("dir", "json"):
        loader = {
            _split: DataLoader(_data, **cfg["dataset"]["dataloader"][_split])
            for _split, _data in data.items()
        }

    elif fmt in ("webdataset", "webdataset-multi"):
        loader = {
            _split: wds.WebLoader(_data, **cfg["dataset"]["webloader"][_split])
            for _split, _data in data.items()
        }

    return data, loader


def initialize_map_datasets(cfg):
    """
    Initialize Map Dataset.
    """
    if cfg["dataset"]["format"] == "json":

        data_path = cfg["dataset"]["path"]

        data = {
            "test": ImageDataset.from_json(
                cfg["dataset"]["json"]["test"],
                data_path,
            )
        }

    elif cfg["dataset"]["format"] == "dir":

        data = {"test": ImageDataset.from_dir(cfg["dataset"]["dir"]["test"])}

    loader = {
        name: DataLoader(dataset, **cfg["dataset"]["dataloader"])
        for name, dataset in data.items()
    }

    return data, loader


def main():
    """
    Loads dataset, dataloaders, trains, validates and saves weights.
    """
    args = parse_args()

    with open(args.cfg_path, "r") as f:
        cfg = toml.load(f)

    # Initialize torch `Dataset` and `DataLoader` instances
    data, loader = initialize_iterable_datasets(cfg)

    # Configure device
    device = validate_device(cfg["device"])

    if device.type == "cpu":
        torch.set_num_interop_threads(4)
        torch.set_num_threads(4)

    model = load_model(**cfg["model"], device=device.type)

    print(device)
    if "wandb" in sys.modules and cfg["use_wandb"] is True:

        os.environ["WANDB_MODE"] = cfg["wandb"]["WANDB_MODE"]

        wandb.init(**cfg["wandb"]["init"])
        wandb.run.name = cfg["wandb"]["name"]
        wandb.watch(model)

    fmt = cfg["dataset"]["format"]

    if fmt in ("json", "dir"):
        kws = {
            _split: {"batch_size": _cfg["batch_size"], "epochs": 1}
            for _split, _cfg in cfg["dataset"]["dataloader"].items()
        }

    elif fmt in ("webdataset", "webdataset-multi"):
        kws = {
            _split: {"batch_size": _cfg["batch_size"], "epochs": 1}
            for _split, _cfg in cfg["dataset"]["webloader"].items()
        }

    for _split, data_loader in loader.items():

        y_preds, y_trues, y_probs = validate_epoch(
            kws[_split],
            data_loader=data_loader,
            model=model,
            epoch=1,
            device=device,
            split="test",
        )

        pred_results = []

        for img_name in y_trues.keys():
            pred_results.append(
                {
                    "image_name": img_name,
                    "y_true": y_trues[img_name],
                    "y_pred": y_preds[img_name],
                    "malevolent_prob": y_probs[img_name],
                }
            )

        _path, _ext = os.path.splitext(cfg["out"]["results_path"])

        results_path = _path + "_" + _split + "_" + _ext

        with open(results_path, "w") as f:
            fieldnames = ["image_name", "y_true", "y_pred", "malevolent_prob"]

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(pred_results)


if __name__ == "__main__":
    main()
