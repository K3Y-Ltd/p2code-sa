from typing import Tuple, List
from numpy.typing import ArrayLike

import os
import itertools
import numpy as np

from PIL import Image


def img_slicers_from_patch_size(
    img: ArrayLike, patch_size: Tuple[int, int]
) -> List[Tuple[slice, slice]]:
    """
    Create image slicers from patch size.

    Parameters
    ----------
    img : ArrayLike
        An image represented as a numpy array with shape (h, w, c).
    patch_size : Tuple[int, int]
        The patch size as a tuple of integers representing height and width.

    Returns
    -------
    List[Tuple[slice, slice]]
        A list of slicer pairs to be used concurrently across the
        Height and the Width dimension.
    """
    row_size, col_size = patch_size
    n_rows, n_cols, _ = img.shape

    rr = itertools.pairwise([idx for idx in range(0, n_rows + 1, row_size)])
    cc = itertools.pairwise([idx for idx in range(0, n_cols + 1, col_size)])

    rr = list(rr)
    cc = list(cc)

    slicers = [
        (slice(j_start, j_end), slice(i_start, i_end))
        for j_start, j_end in rr
        for i_start, i_end in cc
    ]

    return slicers


def img_slicers_from_number_of_splits(
    img: ArrayLike, n_row: int, n_col: int
) -> List[Tuple[slice, slice]]:
    """
    Create image slicers from number of splits.

    Parameters
    ----------
    img : ArrayLike
        An image represented as a numpy array with shape (h, w, c).
    n_row : int
        Number of splits across the Height dimension.
    n_col : int
        Number of splits across the Width dimension.

    Returns
    -------
    List[Tuple[slice, slice]]
        A list of slicer pairs to be used concurrently across the
        Height and the Width dimension.
    """
    ww = [[idx.min(), idx.max()] for idx in np.array_split(range(img.shape[0]), n_row)]
    hh = [[idx.min(), idx.max()] for idx in np.array_split(range(img.shape[1]), n_col)]

    # Handle non-inclusive last index per slice
    slicers = [
        (slice(j_start, j_end + 1), slice(i_start, i_end + 1))
        for j_start, j_end in ww
        for i_start, i_end in hh
    ]

    return slicers


def rescale_image(input_dir: str, output_dir: str) -> None:
    """
    Rescale images using PIL `img.thumbnail` method. Used for testing purposes.
    """
    if input_dir == output_dir:
        raise ValueError("Give different directory for writing out scaled images.")

    size = 128, 128

    for file in os.listdir(input_dir):

        if not file.endswith(".png"):
            continue

        input_path = os.path.join(input_dir, file)

        output_path = os.path.join(output_dir, file)

        try:
            img = Image.open(input_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, format="png")
        except IOError:
            print("cannot create thumbnail for '%s'" % input_path)
