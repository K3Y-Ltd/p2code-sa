import numpy as np

from hilbert import decode

from .base import CurveBase


class HilbertCurve(CurveBase):
    """
    Class to represent a hilbert-based space filling curve.
    """

    def create_layout_map(self):
        """
        Create curve layout map for a given size and dimension.

        Returns
        -------
        np.ndarray
            A numpy array of shape (size**2, 2).
        """
        # In order for the `numpy-hilbert-curve` implementation to match the
        # original `binvis` layout we need to increment the `num_bits` by 1
        # for every case. This is tested against the `binvis` implementation
        # but it is not clear why that is the case.
        num_bits = int(np.log2(self.size)) + 1

        locs = decode(
            np.arange(0, self.size**2, dtype="int32"),
            num_dims=self.dimension,
            num_bits=num_bits,
        )

        return locs.astype("int32")
