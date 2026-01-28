import numpy as np
import cv2
import torch

from torch.utils.data import Dataset

from .utils import _from_dir, _from_json


class ImageDataset(Dataset):
    """
    Constructs the ImageDataset.
    """

    def __init__(self, paths, labels, weights=None, transform=None):
        """
        Initializes the Pytorch dataset class.

        Parameters
        ----------
        paths : List[str]
            A list of image paths.
        labels : List[int]
            A list of (0, 1) integers, where `1` is the positive class.
        weights : List[float]
            A list of floats, one for each class.
        transform : str (Optional)
            Transformations to be applied on the input image data
        """
        super().__init__()

        self.paths = paths
        self.labels = labels

        # transforms are currently switched off
        # self.transform = transform

        if weights is None:
            self.weights = self.calculate_class_weights()
        else:
            self.weights = torch.FloatTensor(weights)

    def calculate_class_weights(self):
        """
        Determine weights to scale loss for class imbalance.
        """
        pos = np.sum(self.labels)

        neg = len(self.labels) - pos

        weights = torch.FloatTensor([1, neg / pos])

        return weights

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index: int):
        """
        Used by the dataloader to form batches and parallelize fetching.

        Parameters
        ----------
        index : int
            Indicates a sample of the dataset

        Returns
        -------
        array : torch.tensor
            Input image tensor.
        label : torch.tensor
            Output classification label.
        weights : torch.tensor
            Global weights computed once at initialization to scale the loss.
        """
        # source and serve the first mri plane
        array = cv2.imread(self.paths[index])

        label = self.labels[index]

        if label == 1:
            label = torch.FloatTensor([[0, 1]])
        elif label == 0:
            label = torch.FloatTensor([[1, 0]])

        array = torch.FloatTensor(array).permute(2, 0, 1)

        return array, label, self.weights

    @classmethod
    def from_json(cls, json_path, data_dir):
        """
        Initialize `ImageDataset` instance from `.json` file.
        """
        paths, labels = _from_json(json_path, data_dir)

        return cls(paths=paths, labels=labels)

    @classmethod
    def from_dir(cls, data_dir):
        """
        Initialize `ImageDataset` instance from path to rood diretory.
        """
        paths, labels = _from_dir(data_dir)

        return cls(paths=paths, labels=labels)
