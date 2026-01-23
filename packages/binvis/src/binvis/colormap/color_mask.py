from typing import List

import numpy as np

from .color_base import DataColorMap


class ColorMask(DataColorMap):
    """
    Class to represent a colormap object that creates a color
    mask on blocks specified by index spans.

    The `ColorMask` instance does not require a byte buffer to
    be initialized as other classes of the `colromap` module,
    but a list of spans and the total length on blocks specified
    by index spans.
    """

    MASK_COLOR = 255

    @classmethod
    def from_spans(cls, n, spans):
        """
        Create a `ColorMask` instance from spans.
        """
        data = cls.build_color_array_with_spans(n, spans)

        return cls(data=data)

    @classmethod
    def build_color_array_with_spans(cls, n, spans):
        """
        Convert spans to 1-channel color values.
        """
        data = bytearray(n)

        try:
            for s, e in spans:
                for idx in range(s, e):
                    data[idx] = cls.MASK_COLOR
        except IndexError:
            raise ValueError("Given array size `n` is smaller than input spans.")

        return bytes(data)
