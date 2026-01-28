from typing import List

import numpy as np

from .iter_color_base import IterableDataColorMap


class IterableColorMixer:
    """
    A class to support mixing colormaps into a single one,
    by stacking them into different channels.

    Input colormaps must have a single channel. The output
    colormap is handled depending on the number of inputs,
    in order to have 3 channels:

    - if no. of colormaps == 1:
        Input colormap is returned in `RGB` mode.

    - if no. of colormaps == 2:
        A `NotImplementedError` is raised.

    - if no. of colormaps == 3:
        Input colormaps are stacked per channel.

    - if no. of colormaps > 3:
        Only the first 3 colormaps are kept.
    """

    def __init__(self, cmaps):
        """
        Initializer for ColorMixer class.

        Parameters
        ----------
        color_maps : List[IterableDataColorMap]
        """
        cmaps = self._validate_cmaps(cmaps)

        self.cmaps = cmaps
        self.n_cmaps = len(cmaps)

        self.size = cmaps[0].size
        self.chunk_size = cmaps[0].chunk_size

    def _validate_cmaps(self, cmaps: List[IterableDataColorMap]):
        """
        Validate input cmaps.
        """
        against = cmaps[0].size

        if not all(cmap.size == against for cmap in cmaps):
            raise ValueError("All cmaps should have the same shape.")

        if len(cmaps) == 2:
            raise NotImplementedError(
                (
                    "Given color maps are two and cannot be handled. "
                    "Specify either one or three color maps."
                )
            )

        if len(cmaps) > 3:
            print(
                (
                    "Given color maps are more than three. Only the "
                    "first three color maps will be used."
                )
            )
            cmaps = cmaps[:3]

        return cmaps

    def __len__(self):
        return len(self.cmaps[0])

    def __iter__(self):
        return self

    def __next__(self):
        return np.stack([next(cmap) for cmap in self.cmaps], axis=1)
