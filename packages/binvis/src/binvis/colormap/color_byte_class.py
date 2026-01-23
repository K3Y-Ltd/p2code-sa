from .color_base import DataColorMap

import string
import numpy as np

CHAR_PRINTABLE = set(string.printable)


class ColorByteClass(DataColorMap):
    """
    Class to represent a `ColorByteClass` colormap object.

    A `ColorByteClass` instance, colors a byte based on its
    value by distinguishing between 4 distinct color classes:
    - byte value == 0
    - byte value == 255
    - byte value could be a printable ascii character
    - byte value does not belong in the above categories.
    """

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
    L = np.array([0, 255, 55, 228], dtype="uint8")

    def get_point(self, idx, mode="RGB"):
        """
        Return color for given byte-array index.

        Parameters
        ----------
        idx : int
            Index to get value of stored byte-array in `self.data`.
        mode : {'RGB', 'L'}
            The shape and format of output colors.
        """
        byte = self.data[idx]

        if byte == 0:
            clr = self.MIN_BYTE_COLOR

        elif byte == 255:
            clr = self.MAX_BYTE_COLOR

        # Same `chr(byte) in CHAR_PRINTABLE` : 9 <= b <= 13 || 32 <= b <= 126
        elif (8 < byte < 14) or (31 < byte < 127):
            clr = self.ASCII_BYTE_COLOR

        else:
            clr = self.OTHER_BYTE_COLOR

        if mode == "RGB":
            return clr

        elif mode == "L":
            return clr[0]

    def get_point_np(self, idx, mode="RGB"):
        """
        Return color for given index. Support `int`, `slice`, `array`

        Parameters
        ----------
        idx : Union[int, slice, ArrayLike]
            Index to get value of stored byte-array in `self.data`.
        mode : {'RGB', 'L'}
            The shape and format of output colors.
        """
        b_arr = self.b_arr[idx]

        if isinstance(idx, int):
            b_arr = b_arr.reshape(1)

        elif isinstance(idx, slice) or isinstance(idx, np.ndarray):
            pass

        else:
            raise ValueError(
                (
                    "`idx` argument must be either of type `int`, `slice` "
                    "or and indexing numpy array."
                )
            )

        # Build masks for MIN_BYTE, MAX_BYTE, ASCII_BYTE.
        # The rest will be OTHER_BYTE
        MASK_MIN = b_arr == 0
        MASK_MAX = b_arr == 255
        MASK_ASCII = (b_arr > 8) & (b_arr < 14) | (b_arr > 31) & (b_arr < 127)

        masks = [MASK_MIN, MASK_MAX, MASK_ASCII]

        # `c_idx` is an array of class labels, one label per byte 
        # The labels correspond to the colors of `self.RGB`, `self.L`
        c_idx = np.full_like(b_arr, fill_value=3)

        for i, mask in enumerate(masks):
            c_idx[mask] = i

        if mode == "RGB":
            return self.RGB[c_idx]

        elif mode == "L":
            c_arr = self.L[c_idx]
            return c_arr[:, np.newaxis]
