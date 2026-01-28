from typing import Tuple, List, Iterator, Callable

import os

import cv2
import torch
import webdataset as wds
import numpy as np

from functools import partial

from torch.utils.data import IterableDataset, ChainDataset
from torch.utils.data.datapipes.iter import IterableWrapper
from torch.utils.data.datapipes.datapipe import IterDataPipe

from torchvision import transforms

from .flat_mapper import FlatMapperIterDataPipe
from .imgproc import img_slicers_from_patch_size
from .utils import _from_json, _get_mask_path, _get_file_name, _from_dir


def label_to_tensor(label: int) -> np.ndarray:
    """
    Map label to tensor.
    """
    if label == 0:
        return np.array([[1, 0]], dtype="float32")

    elif label == 1:
        return np.array([[0, 1]], dtype="float32")


def _img_transforms():
    """
    Get transforms to be applied per patch.
    """
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    return transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )


def _cosoco_classification(img_name, img_patches, lbl_patches, weights, preprocess):
    """
    An iterator for the classification task.
    """
    return [
        (
            img_name,
            patch_id,
            torch.FloatTensor(img_patch).permute(2, 0, 1),
            torch.FloatTensor(label_to_tensor(lbl_patch)),
            torch.FloatTensor(weights),
        )
        for patch_id, (img_patch, lbl_patch) in enumerate(zip(img_patches, lbl_patches))
    ]


def _cosoco_segmentation(img_name, img_patches, msk_patches, weights):
    """
    An iterator for the classification task.
    """
    return [
        (
            img_name,
            patch_id,
            torch.FloatTensor(img_patch).permute(2, 0, 1),
            torch.FloatTensor(msk_patch),
            torch.FloatTensor(weights),
        )
        for patch_id, (img_patch, msk_patch) in enumerate(zip(img_patches, msk_patches))
    ]


def split_sample_into_patches(
    sample: Tuple, task: str, patch_size: Tuple[int, int], weights: List[float]
) -> Iterator[Tuple]:
    """
    Split input image into image patches.

    Parameters
    ----------
    sample : Tuple
        A tuple (image, image mask, metadata).
    task : str
        A flag indicating the supported task: {'classification', 'segmentation'}.
    patch_size : Tuple[int, int]
        A tuple of patch size to extract from input image.

    Yields
    ------
    Tuple[str, int, torch.Tensor, torch.Tensor, torch.Tensor]
        A tuple of image name, patch id, patch image, patch label,
        class weight.
    """
    img, img_msk, _json = sample

    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    img_name = _json["name"]
    img_lbl = 0 if "benign" == _json["label"] else 1

    slicers = img_slicers_from_patch_size(img, patch_size)

    img_patches = [img[slc1, slc2, :] for (slc1, slc2) in slicers]

    msk_patches = [img_msk[slc1, slc2, :] for (slc1, slc2) in slicers]

    if img_lbl == 0:
        lbl_patches = [0] * len(img_patches)

    if img_lbl == 1:
        lbl_patches = [int(patch.any()) for patch in msk_patches]

    preprocess = _img_transforms()

    if task == "classification":
        return _cosoco_classification(
            img_name,
            img_patches=img_patches,
            lbl_patches=lbl_patches,
            weights=weights,
            preprocess=preprocess,
        )

    elif task == "segmentation":
        return _cosoco_segmentation(
            img_name,
            img_patches=img_patches,
            msk_patches=msk_patches,
            weights=weights,
        )


def build_wds_pipeline_data_from_shards(
    shards_path: str, splits: str | List[str], **kwargs
) -> wds.DataPipeline:
    """
    Initialize `webdataset` Iberable Datasets from shards filtered by split.

    Parameters
    ----------
    shards_path : str
        Path to folder where `webdataset` shards are found.
    splits : str | List[str]
        Splits to filter (by name) shards from shards folder.
    **kwargs
        Keyword arguments to be passed to record preprocessing.

    Returns
    -------
    wds.DataPipeline
        A `wds.DataPipeline` over the `webdataset` shards.
    """
    if isinstance(splits, str):
        splits = [splits]

    _preprocess = partial(split_sample_into_patches, **kwargs)

    fs = os.listdir(shards_path)

    dps = []

    for split in splits:

        shard_list = [os.path.join(shards_path, f) for f in fs if split in f]

        dp = wds.DataPipeline(
            # load a list of shard paths
            wds.SimpleShardList(shard_list),
            # shuffle shards
            wds.shuffle(100),
            # split per workers
            wds.split_by_worker,
            # map shard-iterator to tarfile-iterator
            wds.tarfile_to_samples(),
            # decode images to rgb8 numpy array
            wds.decode("rgb8"),
            # map sample to tuple
            wds.to_tuple("png", "mask.png", "json"),
            # Shuffle per image
            wds.shuffle(200),
            # parse sample into List[patches]
            wds.map(_preprocess),
            # flatten unlist
            wds.filters.unlisted(),
        )

        dps.append(dp)

    return ChainDataset(dps)


def build_dp_from_webdataset_train(dataset: wds.DataPipeline) -> IterDataPipe:
    """
    Convert a `wds.DataPipeline` to an `IterDataPipe` instance
    to interact directly with the DataLoader.

    Parameters
    ----------
    dataset : wds.DataPipeline
        A `wds.DataPipeline` over the `webdataset` shards.

    Returns
    -------
    dp : IterDataPipe
        An `IterDataPipe` instance.
    """
    # Convert to DataPipe
    dp = IterableWrapper(dataset)

    return dp


def build_dp_from_webdataset_valid(dataset: wds.DataPipeline) -> IterDataPipe:
    """
    Convert a `wds.DataPipeline` to an `IterDataPipe` instance
    to interact directly with the DataLoader.

    Parameters
    ----------
    dataset : wds.DataPipeline

    Returns
    -------
    dp : IterDataPipe
        An `IterDataPipe` instance.
    """
    # Convert to DataPipe
    dp = IterableWrapper(dataset)

    return dp


def build_dp_from_iterable_dataset_train(dataset: IterableDataset) -> IterDataPipe:
    """
    Convert an `IterableDataset` to an `IterDataPipe` instance
    to interact directly with the DataLoader.

    Parameters
    ----------
    dataset : IterableDataset
        An iterable dataset to wrap with an IterableWrapper.

    Returns
    -------
    dp: IterDataPipe
        An `IterDataPipe` instance.
    """
    func_kw = {"patch_size": dataset.patch_size, "weights": dataset.weights}

    func = partial(extract_patches_from_image_train, **func_kw)

    # Convert to DataPipe
    dp = IterableWrapper(dataset)
    # Add shuffling initial data on the image level & sharding
    dp = dp.shuffle(buffer_size=1000)
    # Apply patch extraction and flatten result
    dp = FlatMapperIterDataPipe(dp, func)
    # Add shuffling on the patch level
    dp = dp.shuffle(buffer_size=1000)

    return dp


def build_dp_from_iterable_dataset_valid(dataset: IterableDataset) -> IterDataPipe:
    """
    Convert an `IterableDataset` to an `IterDataPipe` instance
    to interact directly with the DataLoader.

    Parameters
    ----------
    dataset : IterableDataset
        An iterable dataset to wrap with an IterableWrapper.

    Returns
    -------
    dp: IterDataPipe
        An `IterDataPipe` instance.
    """
    func_kw = {"patch_size": dataset.patch_size, "weights": dataset.weights}

    func = partial(extract_patches_from_image_train, **func_kw)

    # Convert to DataPipe
    dp = IterableWrapper(dataset)
    # Apply patch extraction and flatten result
    dp = FlatMapperIterDataPipe(dp, func)

    return dp


def build_dp_from_iterable_dataset_infer(dataset: IterableDataset) -> IterDataPipe:
    """
    Convert an `IterableDataset` to an `IterDataPipe` instance
    to interact directly with the DataLoader.

    Parameters
    ----------
    dataset : IterableDataset
        An iterable dataset to wrap with an IterableWrapper.

    Returns
    -------
    dp: IterDataPipe
        An `IterDataPipe` instance.
    """
    func_kw = {"patch_size": dataset.patch_size}

    func = partial(extract_patches_from_image_path_infer, **func_kw)

    # Convert to DataPipe
    dp = IterableWrapper(dataset)
    # Apply patch extraction
    dp = FlatMapperIterDataPipe(dp, func)

    return dp


def extract_patches_from_image_train(
    record: Tuple[str, int], patch_size: Tuple[int, int], weights: List[float]
) -> Iterator[Tuple]:
    """
    Extract patches from an (image-path, label) record.

    Parameters
    ----------
    record : Tuple[str, int]
        A tuple with the path to image file and the image's label.
    patch_size : Tuple[int, int]
        The patch size in the width and height direction.
    weights : List[float]
        A list of weights to assign to each class.

    Yields
    ------
    str
        The image's name.
    int
        The patch id.
    torch.Tensor
        The image as a torch tensor array.
    torch.Tensor
        The label as a torch tensor array.
    """
    img_path, label = record

    img = cv2.imread(img_path)

    slicers = img_slicers_from_patch_size(img, patch_size)

    patches = [img[slc1, slc2, :] for (slc1, slc2) in slicers]

    if label == 0:
        labels = [0] * len(patches)

    if label == 1:

        mask_path = _get_mask_path(img_path)

        img_msk = cv2.imread(mask_path)

        img_patches = [img_msk[slc1, slc2, :] for (slc1, slc2) in slicers]

        labels = [int(patch.any()) for patch in img_patches]

    img_name = _get_file_name(img_path)

    for patch_id, (patch, label) in enumerate(zip(patches, labels)):

        if label == 0:
            lbl = np.array([[1, 0]], dtype="float32")
        else:
            lbl = np.array([[0, 1]], dtype="float32")

        yield (
            img_name,
            patch_id,
            torch.FloatTensor(patch).permute(2, 0, 1),
            torch.FloatTensor(lbl),
            torch.FloatTensor(weights),
        )


def extract_patches_from_image_path_infer(
    record: str, patch_size: Tuple[int, int]
) -> Iterator[Tuple]:
    """
    Extract patches from image array.

    Parameters
    ----------
    record : str
        A path to an image file representing a software container.
    patch_size : Tuple[int, int]
        The patch size in the width and height direction.

    Yields
    ------
    int
        The patch id.
    torch.Tensor
        The image as a torch tensor array.
    """
    img_name = _get_file_name(record)

    img = cv2.imread(record)

    slicers = img_slicers_from_patch_size(img, patch_size)

    patches = [img[slc1, slc2, :] for (slc1, slc2) in slicers]

    for patch_id, patch in enumerate(patches):
        yield (img_name, patch_id, torch.FloatTensor(patch).permute(2, 0, 1))


def extract_patches_from_image_np_infer(
    img: np.ndarray, patch_size: Tuple[int, int]
) -> Iterator[Tuple]:
    """
    Extract patches from image array.

    Parameters
    ----------
    img : np.ndarray
        An image as numpy array, loaded with `cv2.imread`.
    patch_size : Tuple[int, int]
        The patch size in the width and height direction.

    Yields
    ------
    int
        The patch id.
    torch.Tensor
        The image as a torch tensor array.
    """
    slicers = img_slicers_from_patch_size(img, patch_size)

    patches = [img[slc1, slc2, :] for (slc1, slc2) in slicers]

    for patch_id, patch in enumerate(patches):
        yield (patch_id, torch.FloatTensor(patch).permute(2, 0, 1))


class ImagePatchIterableDataset(IterableDataset):
    """
    Initializes a torch `IterableDataset` class for training.
    """

    def __init__(
        self,
        paths,
        labels,
        task="classification",
        patch_size=(256, 256),
        weights=[1.0, 256.0],
        transform=None,
    ):
        """
        Initializes the Pytorch dataset class.

        Parameters
        ----------
        paths : List[str]
            Image paths.
        labels : List[int]
            Image labels.
        patch_size : Tuple[int, int]
            The size of the patch to split input image into.
        weights : List[float, float]
            Class weights.
        transform : None | str
            Transformations to be applied on the input image data
        """
        super().__init__()

        self.paths = paths
        self.labels = labels
        self.task = task
        self.patch_size = tuple(patch_size)
        self.weights = weights

        # transforms are currently switched off
        self.transform = transform

    def create_stream(self, paths, labels):
        """
        Create image stream.
        """
        for path, label in zip(paths, labels):
            yield path, label
            # yield from self.extract_patches_from_image(path, label)

    def __iter__(self):
        return self.create_stream(self.paths, self.labels)

    # NOTE: Remove this?
    def __len__(self):
        # This needs to be parametrized to work with arbitrary patch sizes
        return len(self.paths) * 64

    @classmethod
    def from_json(cls, json_path, data_dir, **kwargs):
        """
        Initialize `ImageDataset` instance from `.json` file.
        """
        paths, labels = _from_json(json_path, data_dir)

        return cls(paths=paths, labels=labels, **kwargs)

    @classmethod
    def from_dir(cls, data_dir, **kwargs):
        """
        Initialize `ImageDataset` instance from path to rood diretory.
        """
        paths, labels = _from_dir(data_dir)

        return cls(paths=paths, labels=labels, **kwargs)


class ImagePatchIterableDatasetInfer(IterableDataset):
    """
    Constructs an iterable of the image Dataset.
    """

    def __init__(
        self, paths, task="classification", patch_size=(256, 256), transform=None
    ):
        """
        Initializes a torch `IterableDataset` class for inference.

        Parameters
        ----------
        paths : str | List[str]
            Image paths.
        patch_size : Tuple[int, int]
            The size of the patch to split input image into.
        transform : None | str
            Transformations to be applied on the input image data
        """
        super().__init__()

        if isinstance(paths, str):
            paths = [paths]

        self.paths = paths

        self.task = task
        self.patch_size = tuple(patch_size)

        # transforms are currently switched off
        self.transform = transform

    def create_stream(self, paths):
        """
        Create image stream.
        """
        for path in paths:
            yield path

    def __iter__(self):
        return self.create_stream(self.paths)

    # NOTE: Remove this?
    def __len__(self):
        # This needs to be parametrized to work with arbitrary patch sizes
        return len(self.paths) * 64
