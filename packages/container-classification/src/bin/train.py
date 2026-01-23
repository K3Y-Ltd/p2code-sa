from typing import Dict, Tuple

import os
import sys
import toml
import argparse
import datetime

import torch
import torch.optim as optim
import numpy as np
import webdataset as wds

from torch.utils.data import DataLoader, IterableDataset, ChainDataset

try:
    import wandb
except ImportError:
    print("`wandb` was not found. `wandb` functionalities will be disabled.")

try:
    import intel_extension_for_pytorch as ipex  # type: ignore
except ImportError:
    print(
        (
            "`intel extension for pytorch is not found. "
            "Training with 'intel' gpus is disabled."
        )
    )

from container_classification.dataset import (
    ImagePatchIterableDataset,
)

from container_classification.dataset.iterable_dataset import (
    build_dp_from_iterable_dataset_train,
    build_dp_from_iterable_dataset_valid,
    build_wds_pipeline_data_from_shards,
)

from container_classification.utils import (
    train_epoch,
    validate_epoch,
    model_save,
    validate_device,
)

from container_classification.models import (
    AlexNet,
    ResNet18,
    MobileNetV2,
    SqueezeNet,
    VGG11,
    ShuffleNet,
    EfficientNet,
    ResNext101,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cfg_path",
        type=str,
        help="Path to training configuration `.toml` file.",
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
        "train": build_dp_from_iterable_dataset_train(
            ImagePatchIterableDataset.from_json(
                cfg["dataset"]["json"]["train"], data_path, **kw
            )
        ),
        "valid": build_dp_from_iterable_dataset_valid(
            ImagePatchIterableDataset.from_json(
                cfg["dataset"]["json"]["valid"], data_path, **kw
            )
        ),
        "test": build_dp_from_iterable_dataset_valid(
            ImagePatchIterableDataset.from_json(
                cfg["dataset"]["json"]["test"], data_path, **kw
            )
        ),
    }

    return data


def _initialize_iterable_dataset_dir(cfg: Dict) -> Dict[str, IterableDataset]:
    """
    Initialize an iterable dataset given `dir`.
    """
    kw = cfg["dataset"]["kw"]

    data = {
        "train": build_dp_from_iterable_dataset_train(
            ImagePatchIterableDataset.from_dir(cfg["dataset"]["dir"]["train"], **kw)
        ),
        "valid": build_dp_from_iterable_dataset_valid(
            ImagePatchIterableDataset.from_dir(cfg["dataset"]["dir"]["valid"], **kw)
        ),
        "valid": build_dp_from_iterable_dataset_valid(
            ImagePatchIterableDataset.from_dir(cfg["dataset"]["dir"]["test"], **kw)
        ),
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

    train_split = cfg["dataset"]["splits"]["train"]
    valid_split = cfg["dataset"]["splits"]["valid"]
    test_split = cfg["dataset"]["splits"]["test"]

    data = {
        "train": build_wds_pipeline_data_from_shards(data_path, train_split, **kw),
        "valid": build_wds_pipeline_data_from_shards(data_path, valid_split, **kw),
        "test": build_wds_pipeline_data_from_shards(data_path, test_split, **kw),
    }

    return data


def _initialize_iterable_dataset_webdataset_multi(
    cfg: Dict,
) -> Dict[str, IterableDataset]:
    """
    Initialize an iterable dataset with `.webd` files.
    """
    kw = cfg["dataset"]["kw"]

    data_train = [
        build_wds_pipeline_data_from_shards(_subset["path"], _subset["split"], **kw)
        for _subset in cfg["dataset"]["train"]
    ]

    data_valid = [
        build_wds_pipeline_data_from_shards(_subset["path"], _subset["split"], **kw)
        for _subset in cfg["dataset"]["valid"]
    ]

    data_test = [
        build_wds_pipeline_data_from_shards(_subset["path"], _subset["split"], **kw)
        for _subset in cfg["dataset"]["test"]
    ]

    data = {
        "train": ChainDataset(data_train),
        "valid": ChainDataset(data_valid),
        "test": ChainDataset(data_test),
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
        "webdataset-multi": _initialize_iterable_dataset_webdataset_multi,
    }

    fmt = cfg["dataset"]["format"]

    data = _DATASET_INITIALIZERS[fmt](cfg)

    if fmt in ("dir", "json"):
        loader = {
            "train": DataLoader(data["train"], **cfg["dataset"]["dataloader"]["train"]),
            "valid": DataLoader(data["valid"], **cfg["dataset"]["dataloader"]["valid"]),
            "test": DataLoader(data["test"], **cfg["dataset"]["dataloader"]["valid"]),
        }

    elif fmt in ("webdataset", "webdataset-multi"):
        loader = {
            "train": wds.WebLoader(
                data["train"], **cfg["dataset"]["webloader"]["train"]
            ),
            "valid": wds.WebLoader(
                data["valid"], **cfg["dataset"]["webloader"]["valid"]
            ),
            "test": wds.WebLoader(data["test"], **cfg["dataset"]["webloader"]["valid"]),
        }

    return data, loader


def calculate_class_weights(labels):
    """
    Determine weights to scale loss for class imbalance.
    """
    pos = np.sum(labels)

    neg = len(labels) - pos

    weights = np.array([1, neg / pos], dtype="float32")

    return weights


def init_loss(loss_type="bce-with-logits", **loss_kw):
    """
    Initialize loss class instance.
    """
    LOSS_CLS = {
        "bce-with-logits": torch.nn.BCEWithLogitsLoss,
    }

    loss_cls = LOSS_CLS.get(loss_type)

    if loss_cls is None:
        raise ValueError(
            ("Given `loss_type` argument is not available. " "Choose from {}").format(
                tuple(LOSS_CLS.keys())
            )
        )

    return loss_cls(**loss_kw)


def get_savedir_name(cfg: Dict, add_timestamp: bool = True) -> str:
    """
    Get model `savedir` name.
    """
    model = cfg["train"]["model"]
    fmt = cfg["dataset"]["format"]
    lr = str(cfg["train"]["optim"]["lr"])

    if fmt in ("json", "dir"):
        bs = str(cfg["dataset"]["dataloader"]["train"]["batch_size"])

    elif fmt in ("webdataset", "webdataset-multi"):
        bs = str(cfg["dataset"]["webloader"]["train"]["batch_size"])

    epochs = str(cfg["train"]["epochs"])

    s = "{model}-{fmt}-lr_{lr}-bs_{bs}-epochs_{epochs}".format(
        model=model, fmt=fmt, lr=lr, bs=bs, epochs=epochs
    )

    if add_timestamp is True:
        t = datetime.datetime.now().strftime("%Y-%m-%d|%H:%M:%S")

        return s + "-TS" + t

    return s


def get_kw_from_cfg(cfg: Dict) -> Tuple[Dict, Dict]:
    """
    Get train and validation kwargs from cfg.
    """
    fmt = cfg["dataset"]["format"]

    if fmt in ("json", "dir"):
        bs_train = cfg["dataset"]["dataloader"]["train"]["batch_size"]
        bs_valid = cfg["dataset"]["dataloader"]["valid"]["batch_size"]

    elif fmt in ("webdataset", "webdataset-multi"):
        bs_train = cfg["dataset"]["webloader"]["train"]["batch_size"]
        bs_valid = cfg["dataset"]["webloader"]["valid"]["batch_size"]

    epochs = str(cfg["train"]["epochs"])

    train_kw = {"batch_size": bs_train, "epochs": epochs}
    valid_kw = {"batch_size": bs_valid, "epochs": epochs}

    return train_kw, valid_kw


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

    print(device)

    MODELS = {
        "alexnet": AlexNet,
        "resnet18": ResNet18,
        "mobile_net": MobileNetV2,
        "squeeze_net": SqueezeNet,
        "vgg": VGG11,
        "efficient_net": EfficientNet,
        "shuffle_net": ShuffleNet,
        "resnext101": ResNext101,
    }

    # initialize model, optim and scheduler
    model_cls = MODELS[cfg["train"]["model"]]

    model = model_cls().to(device.type)

    # Disable loss class initialization outside the training loss
    # pos_weight = torch.Tensor(cfg["train"]["loss"]["pos_weight"]).to(device.type)
    # _ = init_loss(pos_weight=pos_weight)

    optimizer = optim.Adam(model.parameters(), **cfg["train"]["optim"])

    if device.type == "xpu":
        model, optimizer = ipex.optimize(
            model, optimizer=optimizer, dtype=torch.float32
        )

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cfg["train"]["epochs"], eta_min=1e-6
    )

    # Use `wandb` logger if specified
    if "wandb" in sys.modules and cfg["use_wandb"] is True:

        os.environ["WANDB_MODE"] = cfg["wandb"]["WANDB_MODE"]

        wandb.init(**cfg["wandb"]["init"], config=cfg)
        wandb.run.name = cfg["wandb"]["name"]
        wandb.watch(model)

    dirname = get_savedir_name(cfg)

    save_dir = os.path.join(cfg["out"]["model_dir"], dirname)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    train_kw, valid_kw = get_kw_from_cfg(cfg)

    # train, val and model save
    for epoch in range(1, cfg["train"]["epochs"] + 1):

        train_epoch(
            train_kw,
            data_loader=loader["train"],
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            device=device,
        )

        _ = validate_epoch(
            valid_kw,
            data_loader=loader["valid"],
            model=model,
            epoch=epoch,
            device=device,
            split="valid",
        )

        save_path = os.path.join(
            save_dir, "{}_ckpt_{}.pth".format(cfg["train"]["model"], epoch)
        )

        model_save(model, optimizer, scheduler, epoch, save_path)

    _ = validate_epoch(
        valid_kw,
        data_loader=loader["test"],
        model=model,
        epoch=epoch,
        device=device,
        split="test",
    )


if __name__ == "__main__":
    main()
