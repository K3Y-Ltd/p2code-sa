import os
import math
import tempfile
import shutil

import numpy as np

from binvis.scurve_np import create_layout_map_from_size
from binvis.colormap_iter import IterableDataColorMap
from binvis.progress import Progress

from PIL import Image


def drawmap_square_iter(
    lmap: str, size: int, cmap: IterableDataColorMap, prog: Progress
) -> Image:
    """
    Draw colormap to a square of specified size with the
    numpy interface.

    Parameters
    ----------
    lmap : str
        A string representing a pixel layoutmap.
    size : int
        The width of the image to be created.
    cmap : DataColorMap
        An instance that is a subclass of `DataColorMap`.
        Should implement the method `.get_point(idx)`.
    prog : Progress
        A `Progress` instance.

    Returns
    -------
    img : Image
        Returns the created `Image`.
    """
    # 1. Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = create_layout_map_from_size(lmap, 2, size)

    # 2. Initialize image array
    w, h = size, size

    img_arr = np.zeros((h, w, 3), dtype=np.uint8)

    # 3. Get step and initialize color indexing array over the target image.
    step = cmap.size / float(size**2)

    idx = np.linspace(
        0, int(size**2 * step), num=size**2, endpoint=False, dtype="int32"
    )

    # 4. Initialize pointers
    arr_s_idx, arr_e_idx, img_idx = 0, 0, 0

    for color_arr in cmap:

        arr_e_idx += len(color_arr)

        # Get slice of index array that corresponds to input `color_arr`.
        s_slc, e_slc = np.searchsorted(idx, (arr_s_idx, arr_e_idx))

        idx_slc = slice(s_slc, e_slc)

        _idx = idx[idx_slc] % cmap.chunk_size

        # Get colors of `color_arr` for indexer.
        color = color_arr[_idx]

        # Get slice of image to assign indexed colors
        img_slc = slice(img_idx, img_idx + len(_idx))

        # Assign colors to image
        img_arr[pixel_layout[img_slc, 1], pixel_layout[img_slc, 0]] = color

        # Update color array index pointer & image pixel pointer
        arr_s_idx = arr_e_idx

        img_idx += len(_idx)

    img = Image.fromarray(img_arr, "RGB")

    return img


def drawmap_unrolled_iter(
    lmap: str,
    size: int,
    cmap: IterableDataColorMap,
    prog: Progress,
    step: int | None = None,
) -> Image:
    """
    Draw colormap unrolled to a 1x4 square with the
    numpy interface.

    Parameters
    ----------
    lmap : str
        A string representing a pixel layoutmap.
    size : int
        The width of the image to be created.
    cmap : DataColorMap
        An instance that is a subclass of `DataColorMap`.
        Should implement the method `.get_point(idx)`.
    prog : Progress
        A `Progress` instance.
    step : int | None
        The sampling step on the image.

    Returns
    -------
    img : Image
        Returns the created `Image`.
    """
    # 1. Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = create_layout_map_from_size(lmap, 2, size)

    # 2. Define the number of pixels in the square part i.e. quad
    quad_size = size**2

    if step is None:
        # 3. Number of squares of (size x size) to fill with data.
        N_QUADS = 4

        # 4. Estimate step
        step = cmap.size / float(quad_size * N_QUADS)

    else:
        # 3. Estimate number of quads for given step
        N_QUADS = math.ceil(cmap.size / (step * quad_size))

    # 4. Initialize image array
    w, h = size, size * N_QUADS

    img_arr = np.zeros((h, w, 3), dtype=np.uint8)

    # Initialize pointers
    arr_s_idx, arr_e_idx, img_idx, quad_idx = 0, 0, 0, 0

    color = None

    # Handle integer overflow if indexer gets largest than 2.147.483.647
    if int(N_QUADS * size**2 * step) < (2**31 - 1):
        DTYPE = "int32"
    else:
        DTYPE = "int64"

    for quad_idx in range(N_QUADS):

        # Initialize starting / ending quad index & indexer
        quad_s_idx = int(quad_idx * size**2 * step)
        quad_e_idx = int((quad_idx + 1) * size**2 * step)

        # This array is used as indexer / sampler of the input color array
        idx = np.linspace(
            quad_s_idx, quad_e_idx, num=size**2, endpoint=False, dtype=DTYPE
        )

        # Copy pixel layout & add offset
        _pixel_layout = np.array(pixel_layout, dtype=DTYPE)
        _pixel_layout[:, 1] += quad_idx * size

        # Add any remaining bytes & colors from previous quad
        # Will be 0 for first iteration
        if arr_s_idx > quad_s_idx:

            # NOTE: This is the same code as below.
            s_slc, e_slc = np.searchsorted(idx, (quad_s_idx, arr_e_idx))

            idx_slc = slice(s_slc, e_slc)

            _idx = idx[idx_slc] % cmap.chunk_size

            color = color_arr[_idx]

            # Get colors for given index
            img_slc = slice(img_idx % quad_size, img_idx % quad_size + len(color))

            # Assign colors to pixels
            img_arr[_pixel_layout[img_slc, 1], _pixel_layout[img_slc, 0]] = color

            img_idx += len(color)

        # Get color arrays until we reach the end of the quad.
        while arr_s_idx < quad_e_idx:

            try:
                color_arr = next(cmap)
            except StopIteration:
                break

            # Update end index based on the color array iter size
            arr_e_idx += len(color_arr)

            # Use as end of slice either the arr_e_idx or the quad stopping index.
            _e_idx = min(arr_e_idx, quad_e_idx)

            # search the closest indexer indices
            s_slc, e_slc = np.searchsorted(idx, (arr_s_idx, _e_idx))

            idx_slc = slice(s_slc, e_slc)

            _idx = idx[idx_slc] % cmap.chunk_size

            # Get colors for given index
            color = color_arr[_idx]

            img_slc = slice(img_idx % quad_size, img_idx % quad_size + len(color))

            # Assign colors to pixels
            img_arr[_pixel_layout[img_slc, 1], _pixel_layout[img_slc, 0]] = color

            img_idx += len(color)

            arr_s_idx = arr_e_idx

    img = Image.fromarray(img_arr, "RGB")

    return img


def drawmap_unrolled_n_iter(
    lmap: str, size: int, cmap: IterableDataColorMap, prog: Progress
) -> Image:
    """
    Draw colormap unrolled to a 1xn square with the
    numpy interface.

    Parameters
    ----------
    lmap : str
        A string representing a pixel layoutmap.
    size : int
        The width of the image to be created.
    cmap : DataColorMap
        An instance that is a subclass of `DataColorMap`.
        Should implement the method `.get_point(idx)`.
    prog : Progress
        A `Progress` instance.

    Returns
    -------
    img : Image
        Returns the created `Image`.
    """
    # Number of squares of (size x size) to fill with data.
    N_QUADS = math.ceil(cmap.size / (size**2))

    # Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = create_layout_map_from_size(lmap, 2, size)

    w, h = size, size * N_QUADS

    tmp_dir = tempfile.mkdtemp()

    try:
        MEMMAP_PATH = os.path.join(tmp_dir, "img_arr_memmap.npy")

        print(MEMMAP_PATH)

        img_arr = np.lib.format.open_memmap(
            MEMMAP_PATH, mode="w+", dtype="uint8", shape=(h, w, 3)
        )

        # 3. Get step size & quad size
        quad_size = size**2

        # Iterate over each square (quad). Since each square
        # has the same layout map, we can calculate it once,
        # and translate it / offset it in the Y direction for
        # each quad.
        # Initialize pointers
        arr_s_idx, arr_e_idx, img_idx, quad_idx = 0, 0, 0, 0

        color = None

        for quad_idx in range(N_QUADS):

            # Initialize starting / ending quad index & indexer
            quad_s_idx = int(quad_idx * size**2)
            quad_e_idx = int((quad_idx + 1) * size**2)

            # Copy pixel layout
            _pixel_layout = np.array(pixel_layout, dtype="int32")
            _pixel_layout[:, 1] += quad_idx * size

            # Add any remaining bytes & colors from previous quad
            # Will be 0 for first iteration
            if arr_s_idx > quad_s_idx:

                # We want the remaining colors representing bytes from `color_arr`
                # So we need a negative slice:
                #    color_arr[-remaining]

                # `remaining` is the difference between the current quad starting
                # index and the ending array index
                remaining = quad_s_idx - arr_e_idx

                slc = slice(remaining, None)

                color = color_arr[slc]

                # Get colors for given index
                img_slc = slice(img_idx % quad_size, img_idx % quad_size + len(color))

                # Create indices
                w_idx = _pixel_layout[img_slc, 1]
                h_idx = _pixel_layout[img_slc, 0]

                # Assign colors to pixels
                _update_img_memmap_arr(img_arr, w_idx, h_idx, color)

                img_idx += len(color)

                arr_s_idx = arr_e_idx

            # Get color arrays until we reach the end of the quad.
            while arr_s_idx < quad_e_idx:

                try:
                    color_arr = next(cmap)
                except StopIteration:
                    break

                arr_e_idx += len(color_arr)

                # Use as end of slice either the arr_e_idx or the quad stopping index.
                _e_idx = min(arr_e_idx, quad_e_idx)

                slc = slice(0, _e_idx - arr_s_idx)

                # Get colors for given index
                color = color_arr[slc]

                img_slc = slice(img_idx % quad_size, img_idx % quad_size + len(color))

                # Create indices
                w_idx = _pixel_layout[img_slc, 1]
                h_idx = _pixel_layout[img_slc, 0]

                # Assign colors to pixels
                _update_img_memmap_arr(img_arr, w_idx, h_idx, color)

                img_idx += len(color)

                arr_s_idx = arr_e_idx

        img = Image.fromarray(img_arr, "RGB")

    except Exception as e:
        print(e)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return img


def _update_img_memmap_arr(img_arr, w_idx, h_idx, color):
    """
    Update img memmap array.
    """
    img_arr[w_idx, h_idx] = color

    img_arr.flush()
