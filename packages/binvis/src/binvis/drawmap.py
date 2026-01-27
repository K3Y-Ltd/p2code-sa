import math

from binvis.scurve import fromSize
from binvis.colormap import DataColorMap
from binvis.progress import Progress

from PIL import Image, ImageDraw


def drawmap_square(
    lmap: str, size: int, cmap: DataColorMap, prog: Progress
) -> Image:
    """
    Draw colormap to a square of specified size.

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
    None
        Saves image to disk.
    """
    prog.set_target((size**2))

    lmap = fromSize(lmap, 2, size**2)

    img = Image.new("RGB", (size, size), color=0)

    img_draw = ImageDraw.Draw(img)

    step = len(cmap) / float(len(lmap))

    # Get pixel layout for the square-size image
    pixel_layout = [tuple(pixel) for pixel in lmap]

    for idx, pixel in enumerate(pixel_layout):
        color = cmap.get_point(int(idx * step))

        img_draw.point(pixel, fill=color)

        if not idx % 100:
            prog.tick(idx)

    return img


def drawmap_unrolled(
    lmap: str, size: int, cmap: DataColorMap, prog: Progress
) -> Image:
    """
    Draw colormap unrolled to a 1x4 square.

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
    None
        Creates image and saves to disk.
    """
    prog.set_target((size**2) * 4)

    lmap_obj = fromSize(lmap, 2, size**2)

    img = Image.new("RGB", (size, size * 4), color=0)

    img_draw = ImageDraw.Draw(img)

    step = len(cmap) / float(len(lmap_obj) * 4)

    # Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = [tuple(pixel) for pixel in lmap_obj]

    sofar = 0

    # Iterate over each square (quad). Since each square
    # has the same layout map, we can calculate it once,
    # and translate it / offset it in the Y direction for
    # each quad.

    for quad_idx in range(4):
        quad_offset = quad_idx * size**2

        for i, pixel in enumerate(pixel_layout):
            idx = int(i + quad_offset)

            if idx >= len(cmap):
                break

            color = cmap.get_point(int(idx * step))

            x, y = tuple(pixel)

            img_draw.point((x, y + (size * quad_idx)), fill=tuple(color))

            if not sofar % 100:
                prog.tick(sofar)
            sofar += 1

    return img


def drawmap_unrolled_n(
    lmap: str, size: int, cmap: DataColorMap, prog: Progress
) -> Image:
    """
    Draw colormap unrolled to a 1xn square.

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
    None
        Saves image to disk.
    """
    # Number of squares of (size x size) to fill with data.
    n_quads = math.ceil(len(cmap) / (size**2))

    prog.set_target((size**2) * n_quads)

    lmap_obj = fromSize(lmap, 2, size**2)

    img = Image.new("RGB", (size, size * n_quads), color=0)

    img_draw = ImageDraw.Draw(img)

    # Get pixel layout for a square part of image
    print("Generating Pixel Layout for map `{}`.".format(lmap))
    pixel_layout = [tuple(pixel) for pixel in lmap_obj]

    sofar = 0

    # Iterate over each square (quad). Since each square
    # has the same layout map, we can calculate it once,
    # and translate it / offset it in the Y direction for
    # each quad.

    for quad_idx in range(n_quads):
        quad_offset = quad_idx * size**2

        for i, pixel in enumerate(pixel_layout):
            idx = int(i + quad_offset)

            if idx >= len(cmap):
                break

            color = cmap.get_point(idx)

            x, y = tuple(pixel)

            img_draw.point((x, y + (size * quad_idx)), fill=tuple(color))

            if not sofar % 100:
                prog.tick(sofar)
            sofar += 1

    return img
