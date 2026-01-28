import math
import numpy as np

from binvis.scurve_np import create_layout_map_from_size
from binvis.colormap import DataColorMap
from binvis.progress import Progress

from PIL import Image


def drawmap_square_np(
    lmap: str, size: int, cmap: DataColorMap, prog: Progress
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
    step = len(cmap) / float(size**2)

    # Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = create_layout_map_from_size(lmap, 2, size)

    w, h = size, size
    data = np.zeros((h, w, 3), dtype=np.uint8)

    # Index
    start = 0
    stop = int(size**2 * step)

    idx = np.linspace(start, stop, num=size**2, endpoint=False, dtype="int32")

    # Get colors for given index
    color = cmap.get_point_np(idx)

    # Copy layout array and add offset
    _pixel_layout = np.array(pixel_layout, dtype="int32")

    # Assign colors to pixels
    data[_pixel_layout[:, 1], _pixel_layout[:, 0]] = color

    img = Image.fromarray(data, "RGB")

    return img


def drawmap_unrolled_np(
    lmap: str, size: int, cmap: DataColorMap, prog: Progress, step: int | None = None
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
        step = len(cmap) / float(quad_size * N_QUADS)

    else:
        # 3. Estimate number of quads for given step
        N_QUADS = math.ceil(len(cmap) / (step * quad_size))

    # 4. Initialize image array
    w, h = size, size * N_QUADS

    img_arr = np.zeros((h, w, 3), dtype=np.uint8)

    for quad_idx in range(N_QUADS):

        start = int(quad_idx * size**2 * step)
        stop = int(start + size**2 * step)

        idx = np.linspace(start, stop, num=size**2, endpoint=False, dtype="int32")

        # Handle last quad
        if stop > len(cmap):
            mask = idx >= len(cmap)
            idx[mask] = 0

        # Get colors for given index
        color = cmap.get_point_np(idx)

        # Handle last quad
        if stop > len(cmap):
            color[mask] = np.array([0, 0, 0], dtype="uint8")

        # Copy layout array and add offset
        _pixel_layout = np.array(pixel_layout, dtype="int32")
        _pixel_layout[:, 1] += quad_idx * size

        # Assign colors to pixels
        img_arr[_pixel_layout[:, 1], _pixel_layout[:, 0]] = color

    img = Image.fromarray(img_arr, "RGB")

    return img


def drawmap_unrolled_n_np(
    lmap: str, size: int, cmap: DataColorMap, prog: Progress
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
    n_quads = math.ceil(len(cmap) / (size**2))

    # Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = create_layout_map_from_size(lmap, 2, size)

    w, h = size, size * n_quads
    data = np.zeros((h, w, 3), dtype=np.uint8)

    # Iterate over each square (quad). Since each square
    # has the same layout map, we can calculate it once,
    # and translate it / offset it in the Y direction for
    # each quad.
    for quad_idx in range(n_quads):

        start = quad_idx * size**2
        stop = (quad_idx + 1) * size**2

        slc_colors = slice(start, stop, None)

        # Get colors for given index
        color = cmap.get_point_np(slc_colors)

        slc_pixels = slice(0, len(color))

        # Copy layout array and add offset
        _pixel_layout = np.array(pixel_layout, dtype="int32")
        _pixel_layout[:, 1] += quad_idx * size

        # Assign colors to pixels
        data[_pixel_layout[slc_pixels, 1], _pixel_layout[slc_pixels, 0]] = color

    img = Image.fromarray(data, "RGB")

    return img
