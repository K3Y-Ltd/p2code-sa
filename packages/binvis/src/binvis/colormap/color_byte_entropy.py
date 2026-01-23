import numpy as np

from .color_base import DataColorMap
from .utils import (
    calculate_entropy,
    calculate_entropy_np, 
    get_window_slice,
    calculate_entropy_np_sliding_window,
)


class ColorByteEntropy(DataColorMap):
    """
    Class to represent an `ColorEntropy` colormap object.

    A `ColorEntropy` instance, colors a byte based on its entropy,
    as is calculated on a sliding window on the bytearray with
    given input as a center.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializer for `ColorByteEntropy` class.
        """
        super().__init__(*args, **kwargs)
        self.symbol_map = self.extract_symbol_map(self.data)

    def extract_symbol_map(self, data):
        """
        Index all unique symbols in data.
        """
        symbol_set = list(set(data))
        symbol_set.sort()
        return {symbol: idx for (idx, symbol) in enumerate(symbol_set)}

    def curve(self, v):
        """
        Remap entropy values (?)
        """
        # http://www.wolframalpha.com/input/?i=plot+%284%28x-0.5%29-4%28x-0.5%29**2%29**4+from+0.5+to+1
        f_v = (4 * v - 4 * v**2) ** 4
        f_v = max(f_v, 0)
        return f_v

    def get_point(self, idx, mode="RGB"):
        """
        Return color for given byte-array index.

        Parameters
        ----------
        idx : int
            Index to get value of stored byte-array in `self.data`.
        """
        entropy = calculate_entropy(self.data, 32, idx, len(self.symbol_map))

        r = self.curve(entropy - 0.5) if entropy > 0.5 else 0

        b = entropy**2

        if mode == "RGB":
            return (int(255 * r), 0, int(255 * b))

        elif mode == "L":
            return r

    def get_point_np(self, idx, mode="RGB"):
        """
        Return color for given byte-array index.

        Parameters
        ----------
        idx : int
            Index to get value of stored byte-array in `self.data`.
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
        
        e_s = calculate_entropy_np_sliding_window(b_arr, 32, 256)
        e_s = e_s[:, np.newaxis]

        r_s = (e_s * 255).astype("uint8")

        if mode == "RGB":
            g_s = np.zeros_like(e_s, dtype="uint8")
            b_s = ((e_s**2) * 255).astype("uint8")

            return np.hstack([r_s, g_s, b_s], dtype="uint8")

        elif mode == "L":
            return r_s
