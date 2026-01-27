import math
import numpy as np

from .base import CurveBase


class ZigZagCurve(CurveBase):
    """
    A class representing an n-dimensional zig-zag curve.

    The curve snakes through the n-cube, with each point
    differing from the previous point by exactly one.
    """

    def create_layout_map(self):
        """
        Create curve layout map for a given size and dimension.
        
        Returns
        -------
        np.ndarray
            A numpy array of shape (size**2, 2).
        """
        if self.dimension != 2:
            raise NotImplementedError(
                "The scurve or zigzag layout map is implemented only for 2 dimensions"
            )

        total = self.size**self.dimension
        y = np.arange(total, dtype="int32").reshape(self.dimension * (self.size,))

        y = y % self.size

        locs = np.stack((y.T, y), axis=-1)

        # Reverse every 2
        for i in range(1, self.size, 2):
            locs[i] = np.flipud(locs[i])

        return locs.reshape(-1, self.dimension)
