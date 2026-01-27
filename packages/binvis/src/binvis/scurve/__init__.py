from .hilbert import Hilbert
from .hcurve import Hcurve
from .zigzag import ZigZag
from .zorder import ZOrder
from .natural import Natural
from .graycurve import GrayCurve


curveMap = {
    "hcurve": Hcurve,
    "hilbert": Hilbert,
    "zigzag": ZigZag,
    "zorder": ZOrder,
    "natural": Natural,
    "gray": GrayCurve,
}
curves = curveMap.keys()


def fromSize(curve, dimension, size):
    """
    A convenience function for creating a specified curve by specifying
    size and dimension. All curves implement this common interface.
    """
    return curveMap[curve].fromSize(dimension, size)


def fromOrder(curve, dimension, order):
    """
    A convenience function for creating a specified curve by specifying
    order and dimension. All curves implement this common interface, but
    the meaning of "order" may differ for each curve.
    """
    return curveMap[curve](dimension, order)
