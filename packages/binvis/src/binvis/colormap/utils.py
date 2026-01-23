from numpy.typing import ArrayLike

import math
import scipy
import numpy as np

from functools import partial

from collections import Counter


def get_window_slice(idx: int, data_size: int, window_size: int = 32) -> slice:
    """
    Slice array based on index and size of sliding window.

    Parameters
    ----------
    idx : int
        The offset from the start of the array to extract
        window from.
    data_size : np.ndarray
        A byte array to extract a block of size `window_size`.
    window_size : int
        The size of the window to extract.

    Returns
    -------
    slc : slice
        A slice object to slice the window of interest from the array.
    """
    if window_size % 2 == 0:
        mid = window_size // 2
    else:
        mid = window_size // 2 + 1

    # `idx` is at the start of the array
    if idx < mid:
        s = 0
        e = idx + mid

    # `idx` is at the end of the array
    elif idx > data_size - mid:
        s = idx - mid
        e = data_size

    # `idx` is at the start of the array
    else:
        s = idx - mid
        e = s + window_size

    return slice(s, e, None)


def calculate_entropy_np(
    data: ArrayLike, window_size: int = 32, n_symbols: int = 256
) -> float:
    """
    Calculates entropy for an input numpy array.

    Parameters
    ----------
    data : np.ndarray
        An array to calculate entropy on.
    window_size : int
        The window size to calculate entropy.
    n_symbols : int
        Total number of available symbols in the byte array.

    Returns
    -------
    entropy : float
        The entropy value for input byte array.
    """
    # If blocksize < 256, the number of possible byte values is restricted.
    # In that case, we adjust the log base to make sure we get a value
    # between 0 and 1.
    log_base = min(len(data), window_size, n_symbols)

    return scipy.stats.entropy(np.bincount(data), base=log_base)


def calculate_entropy_np_sliding_window(
    data: ArrayLike, window_size: int = 32, n_symbols: int = 256
) -> float:
    """
    Calculate entropy with sliding window.
    """
    func = partial(np.bincount, minlength=n_symbols)

    # If blocksize < 256, the number of possible byte values is restricted.
    # In that case, we adjust the log base to make sure we get a value
    # between 0 and 1.
    log_base = min(len(data), window_size, n_symbols)

    # Handle start, end pads
    if window_size % 2 == 0:
        s_pad_size = mid = window_size // 2
        e_pad_size = mid - 1
    else:
        s_pad_size = e_pad_size = window_size // 2

    s_pad = np.zeros(s_pad_size, dtype=data.dtype)
    e_pad = np.zeros(e_pad_size, dtype=data.dtype)

    # Handle data main part
    padded = np.concatenate([s_pad, data, e_pad])

    data_strided = np.lib.stride_tricks.sliding_window_view(padded, window_size)

    data_bincount = np.apply_along_axis(func, axis=1, arr=data_strided)

    return scipy.stats.entropy(data_bincount, axis=1, base=log_base)


def calculate_entropy(data, blocksize, offset, symbols=256):
    """
    Returns local byte entropy for a location in a file.

    Parameters
    ----------
    data : bytes
        A byte array to calculate entropy on.
    blocksize : int
        The window size to calculate entropy.
    offset : int
        The offset from the start of the array to calculate
        entropy.
    symbols : int
        Total number of available symbols in the byte array.

    Returns
    -------
    entropy : float
        The entropy value for input byte array.
    """
    # This part decides how the sliding window is calculated on the data.
    if len(data) < blocksize:
        raise ValueError("Data length must be larger than block size.")

    if offset < blocksize // 2:
        start = 0

    elif offset > len(data) - blocksize // 2:
        start = len(data) - blocksize // 2

    else:
        start = offset - blocksize // 2

    hist = {}

    for i in data[start : start + blocksize]:
        hist[i] = hist.get(i, 0) + 1

    base = min(blocksize, symbols)

    entropy = 0

    for i in hist.values():
        p = i / float(blocksize)
        # If blocksize < 256, the number of possible byte values is restricted.
        # In that case, we adjust the log base to make sure we get a value
        # between 0 and 1.
        entropy += p * math.log(p, base)

    return entropy


def parse_color_hex(clr):
    """
    Parse an HTML-style color specification.

    A hexadecimal color is specified with: #RRGGBB, where
    the RR (red),the GG (green) and the BB (blue) hexadecimal
    integers specify the components of the color.
    """
    try:
        r = int(clr[0:2], 16) / 255.0
        g = int(clr[2:4], 16) / 255.0
        b = int(clr[4:6], 16) / 255.0
        return [r, g, b]
    except Exception:
        print(
            (
                "Parsing failed. A color needs to be specified in "
                "an html-style hexadecimal format as a 6-character "
                "string of the form `RRGGBB`. A default color will "
                "be returned `[255, 0, 0]`."
            )
        )
        return [255, 0, 0]
