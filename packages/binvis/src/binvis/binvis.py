#!/usr/bin/env python
from typing import List, Tuple, ByteString, Union

from PIL import Image

from binvis.progress import Progress, Dummy

from binvis.colormap import (
    ColorByteClass,
    ColorByteValue,
    ColorByteEntropy,
    ColorBlock,
    ColorMixer,
    ColorMask,
    ColorTarFileStructure,
)

from binvis.drawmap_np import (
    drawmap_square_np,
    drawmap_unrolled_np,
    drawmap_unrolled_n_np,
)


COLORMAPS = {
    "class": ColorByteClass,
    "magnitude": ColorByteValue,
    "entropy": ColorByteEntropy,
    "structure": ColorTarFileStructure,
}


def visualize_binary(
    byte_array: ByteString,
    size: int = 256,
    color_map: Union[str, List[str]] = ["class"],
    layout_map: str = "hilbert",
    layout_type: str = "unrolled",
    color_block: str = None,
    show_progress: bool = True,
    step: int | None = None,
) -> Image:
    """
    Build an image from a byte array.

    Parameters
    ----------
    byte_array : ByteString
        An array of bytes of type `bytes`.
    size : int
        The width of the image to be created.
    color_map : Union[str, List[str]]
        A string that points to a subclass of `DataColorMap`.
        which should implement the method `.get_point(idx)`.
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
        cmap = cmap_cls(byte_array)

    elif isinstance(color_map, list):

        if len(color_map) == 1:
            cmap_cls = COLORMAPS[color_map[0]]
            cmap = cmap_cls(byte_array)
        else:
            cmap_classes = [COLORMAPS[cmap] for cmap in color_map]
            cmaps = [cmap_class(byte_array) for cmap_class in cmap_classes]
            cmap = ColorMixer(cmaps)

    if show_progress is False:
        prog = Dummy()
    else:
        prog = Progress(None)

    if layout_type == "square":
        img = drawmap_square_np(layout_map, size, cmap, prog)

    elif layout_type == "unrolled":
        img = drawmap_unrolled_np(layout_map, size, cmap, prog, step=step)

    elif layout_type == "unrolled_n":
        img = drawmap_unrolled_n_np(layout_map, size, cmap, prog)

    prog.clear()

    return img


def build_mask_from_spans(
    n_bytes: int,
    spans: List[Tuple[int, int]] = [],
    size: int = 256,
    layout_map: str = "hilbert",
    layout_type: str = "unrolled_n",
    show_progress: bool = True,
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
    step : int
        This argument is valid only for the `unrolled` layout type. The
        step size indicates the sampling step of the underlying byte array.
        When the step is given the image height is adjusted accordingly.

    Returns
    -------
    img : Image
        A PIL `Image` instance.
    """
    cmap = ColorMask.from_spans(n=n_bytes, spans=spans)

    if show_progress is False:
        prog = Dummy()
    else:
        prog = Progress(None)

    if layout_type == "square":
        img = drawmap_square_np(layout_map, size, cmap, prog)

    elif layout_type == "unrolled":
        img = drawmap_unrolled_np(layout_map, size, cmap, prog, step=step)

    elif layout_type == "unrolled_n":
        img = drawmap_unrolled_n_np(layout_map, size, cmap, prog)

    prog.clear()

    return img
