from .hilbert import HilbertCurve
from .zigzag import ZigZagCurve

curve_maps = {
    "hilbert": HilbertCurve,
    "zigzag": ZigZagCurve,
}


def create_layout_map_from_size(curve, dimension, size):
    """
    Create a layout map from size.
    """
    curve_class = curve_maps.get(curve)

    if curve_class is None:
        raise NotImplementedError(
            "`curve` argument {} is not implemented yet. Choose from {}".format(
                curve, curve_maps.keys()
            )
        )

    curve_instance = curve_class(size=size, dimension=dimension)

    return curve_instance.create_layout_map()
