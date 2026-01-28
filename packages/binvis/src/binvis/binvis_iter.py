#!/usr/bin/env python
from typing import List, Tuple, ByteString, Union

from PIL import Image

from binvis.progress import Progress, Dummy

from binvis.colormap_iter import (
    IterableColorByteClass,
    IterableColorByteValue,
    IterableColorTarFileStructure,
    IterableColorMask,
    IterableColorMixer,
)

from binvis.drawmap_iter import (
    drawmap_square_iter,
    drawmap_unrolled_iter,
    drawmap_unrolled_n_iter,
)


COLORMAPS = {
    "class": IterableColorByteClass,
    "magnitude": IterableColorByteValue,
    "structure": IterableColorTarFileStructure,
}


def visualize_binary_iter(
    path: str,
    size: int = 256,
    color_map: Union[str, List[str]] = ["class"],
    layout_map: str = "hilbert",
    layout_type: str = "unrolled",
    color_block: str = None,
    show_progress: bool = True,
    chunk_size: int = 512 * 512,
    step: int | None = None,
) -> Image:
    """
    Build an image from a binary file in a streaming fashion.

    Parameters
    ----------
    path : str
        Path to file to be converted to an image.
    size : int
        The width of the image to be created.
    color_map : Union[str, List[str]]
        A string that points to a subclass of `IterableDataColorMap`.
    layout_map : str
        A string representing a pixel layoutmap.
    layout_type : {'square', 'unrolled', 'unrolled_n'}
        The output image size & aspect ratio. Each type does the
        following:

        - `square` builds an image of dimensions (size, size). Data
           are either stretched or sampled to fit output image.

        - `unrolled` builds an image of dimensions (size, size * 4).
           Data are either stretched or sampled to fit output image.

        - `unrolled_n` builds an image of dimensions (size, size * n)
           where n depends on the number of squares required to fit
           all data. No information is lost with this type. The final
           square is padded with black pixels.

    color_block : str
        Mark a block of data with a specified color. For a block the
        expected format is: hexstartaddr:hexendaddr[:hexcolor]",
    show_progress : bool
        Whether to show progress.
    chunk_size : int
        The iterator maximum chunk size.
    step : int
        This argument is valid only for the `unrolled` layout type. The
        step size indicates the sampling step of the underlying byte array.
        When the step is given the image height is adjusted accordingly.

    Returns
    -------
    img : Image
        A PIL `Image` instance.
    """
    # TODO:
    # Change how color block works if necessary
    if color_block:
        pass

    if isinstance(color_map, str):
        cmap_cls = COLORMAPS[color_map]
        cmap = cmap_cls(path, chunk_size=chunk_size)
        cmap = IterableColorMixer([cmap])

    elif isinstance(color_map, list):

        cmap_clss = [COLORMAPS[cmap] for cmap in color_map]
        cmaps = [cmap_cls(path, chunk_size=chunk_size) for cmap_cls in cmap_clss]
        cmap = IterableColorMixer(cmaps)

    if show_progress is False:
        prog = Dummy()
    else:
        prog = Progress(None)

    if layout_type == "square":
        img = drawmap_square_iter(layout_map, size, cmap, prog)

    elif layout_type == "unrolled":
        img = drawmap_unrolled_iter(layout_map, size, cmap, prog, step=step)

    elif layout_type == "unrolled_n":
        img = drawmap_unrolled_n_iter(layout_map, size, cmap, prog)

    prog.clear()

    return img


def build_iter_mask_from_spans(
    n_bytes: int,
    spans: List[Tuple[int, int]] = [],
    size: int = 256,
    layout_map: str = "hilbert",
    layout_type: str = "unrolled_n",
    show_progress: bool = True,
    chunk_size: int = 512 * 512,
    step: int | None = None,
) -> Image:
    """
    Build a mask

    Parameters
    ----------
    n_bytes : int
        The total number of bytes. The total size of the file related
        to the mask.
    spans : List[Tuple[int, int]]
        A list of spans to map via the layout map onto the mask image.
    size : int
        The width of the image to be created.
    layout_map : str
        A string representing a pixel layoutmap.
    layout_type : {'square', 'unrolled', 'unrolled_n'}
        The output image size & aspect ratio. Each type does the
        following:

        - `square` builds an image of dimensions (size, size). Data
           are either stretched or sampled to fit output image.

        - `unrolled` builds an image of dimensions (size, size * 4).
           Data are either stretched or sampled to fit output image.

        - `unrolled_n` builds an image of dimensions (size, size * n)
           where n depends on the number of squares required to fit
           all data. No information is lost with this type. The final
           square is padded with black pixels.
    show_progress : bool
        Whether to show progress.
    chunk_size : int
        The iterator maximum chunk size.
    step : int
        This argument is valid only for the `unrolled` layout type. The
        step size indicates the sampling step of the underlying byte array.
        When the step is given the image height is adjusted accordingly.

    Returns
    -------
    img : Image
        A PIL `Image` instance.
    """
    cmap = IterableColorMask(size=n_bytes, spans=spans, chunk_size=chunk_size)

    if show_progress is False:
        prog = Dummy()
    else:
        prog = Progress(None)

    if layout_type == "square":
        img = drawmap_square_iter(layout_map, size, cmap, prog)

    elif layout_type == "unrolled":
        img = drawmap_unrolled_iter(layout_map, size, cmap, prog, step=step)

    elif layout_type == "unrolled_n":
        img = drawmap_unrolled_n_iter(layout_map, size, cmap, prog)

    prog.clear()

    return img
