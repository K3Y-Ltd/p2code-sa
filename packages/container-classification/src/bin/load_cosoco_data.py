from typing import Dict

import toml
import argparse
import webdataset as wds

from torch.utils.data import DataLoader, IterableDataset, ChainDataset

from container_classification.dataset.iterable_dataset import (
    build_wds_pipeline_data_from_shards,
    build_dp_from_webdataset_train,
    build_dp_from_webdataset_valid,
)


def parse_args():
    """
    Parse arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cfg_path",
        type=str,
        help="Path to configuration file for data loading.",
    )

    args = parser.parse_args()

    return args


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
        "train": build_dp_from_webdataset_train(
            build_wds_pipeline_data_from_shards(data_path, train_split, **kw)
        ),
        "valid": build_dp_from_webdataset_valid(
            build_wds_pipeline_data_from_shards(data_path, valid_split, **kw)
        ),
        "test": build_dp_from_webdataset_valid(
            build_wds_pipeline_data_from_shards(data_path, test_split, **kw)
        ),
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
        "webdataset": _initialize_iterable_dataset_webdataset_single,
        "webdataset-multi": _initialize_iterable_dataset_webdataset_multi,
    }

    fmt = cfg["dataset"]["format"]

    data = _DATASET_INITIALIZERS[fmt](cfg)

    loader = {
        "train": wds.WebLoader(data["train"], **cfg["dataset"]["webloader"]["train"]),
        "valid": wds.WebLoader(data["valid"], **cfg["dataset"]["webloader"]["valid"]),
        "test": wds.WebLoader(data["test"], **cfg["dataset"]["webloader"]["valid"]),
    }

    return data, loader


def main():
    """
    Main functionality.
    """
    args = parse_args()

    with open(args.cfg_path, "r") as f:
        cfg = toml.load(f)

    ds, ds_loader = initialize_iterable_datasets(cfg)

    for sample in ds:
        # do something
        break

    print(sample)


if __name__ == "__main__":
    main()
