from .iter_color_base import IterableDataColorMap

import string
import numpy as np

CHAR_PRINTABLE = set(string.printable)


class IterableColorByteClass(IterableDataColorMap):
    """
    Class to represent an `IterableDataColorMap` colormap instance.

    An `IterableColorByteClass` instance, allows to iterate over a byte 
    array and color bytes based on their values by distinguishing between 
    four distinct byte classes:
    - `min`:   byte value == 0
    - `max`:   byte value == 255
    - `ascii`: byte value could be a printable ascii character
    - `other`: byte value does not belong in one of the above categories.

    Each class is then mapped to a unique color channel value:
    - `min`: 0
    - `max`: 255
    - `ascii`: 55
    - `other`: 28
    """
    L = np.array([0, 255, 55, 228], dtype="uint8")

    # NOTE: NOT USED in current implementation of the `IterableColorByteClass`.
    MIN_BYTE_COLOR = (0, 0, 0)  # black
    MAX_BYTE_COLOR = (255, 255, 255)  # white
    ASCII_BYTE_COLOR = (55, 126, 184)  # blue
    OTHER_BYTE_COLOR = (228, 26, 28)  # red

    RGB = np.array(
        [
            [0, 0, 0],
            [255, 255, 255],
            [55, 126, 184],
            [228, 26, 28],
        ],
        dtype="uint8",
    )

    def __next__(self):
        return self._color_to_class(next(self.iterator))

    def _color_to_class(self, b_arr: np.ndarray) -> np.ndarray:
        """
        Convert color to class.
        """
        # Build masks for MIN_BYTE, MAX_BYTE, ASCII_BYTE.
        # The rest will be OTHER_BYTE
        MASK_MIN = b_arr == 0
        MASK_MAX = b_arr == 255
        # Same `chr(byte) in CHAR_PRINTABLE` : 9 <= b <= 13 || 32 <= b <= 126
        MASK_ASCII = (b_arr > 8) & (b_arr < 14) | (b_arr > 31) & (b_arr < 127)

        masks = [MASK_MIN, MASK_MAX, MASK_ASCII]

        # `c_idx` is an array of class labels, one label assigned per byte
        c_idx = np.full_like(b_arr, fill_value=3)

        for i, mask in enumerate(masks):
            c_idx[mask] = i

        # Each label is assigned to different `self.L` colors.
        return self.L[c_idx]
