import numpy as np


class ColorMixer:
    """
    A class to support mixing colormaps into a single one,
    by stacking them into different channels. 
    
    Input colormaps must have a single channel. The output
    colormap is handled depending on the number of inputs,
    in order to have 3 channels:
    
    - if no. of colormaps == 1:
        Input colormap is returned in `RGB` mode.
        
    - if no. of colormaps == 2:
        Input colormaps are stacked per channel with a blank
        channel added at the end.
        
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
        color_maps : List[DataColorMap]
        """
        self._validate_cmaps(cmaps)

        self.cmaps = cmaps
        self.n_cmaps = len(cmaps)

    def _validate_cmaps(self, cmaps):
        """
        Validate input cmaps.
        """
        against = cmaps[0].get_shape()

        if not all(cmap.get_shape() == against for cmap in cmaps):
            raise ValueError("All cmaps should have the same shape.")

    def __len__(self):
        return len(self.cmaps[0])

    def get_point(self, idx):
        """
        Return color for given byte-array index.

        Parameters
        ----------
        idx : int
            Index to get value of stored byte-array in `self.data`.
        """
        if len(self.cmaps) == 1:
            return self.cmaps[0].get_point(idx)

        c = tuple(cmap.get_point(idx)[0] for cmap in self.cmaps)

        if self.n_cmaps == 2:
            return c + (0,)

        elif self.n_cmaps == 3:
            return c

        elif self.n_cmaps == 4:
            return c[:3]

    def get_point_np(self, idx):
        """
        Return color for given byte-array index.

        Parameters
        ----------
        idx : int
            Index to get value of stored byte-array in `self.data`.
        """
        if len(self.cmaps) == 1:
            return self.cmaps[0].get_point_np(idx, mode="RGB")

        c_s = [cmap.get_point_np(idx, mode="L") for cmap in self.cmaps]

        if self.n_cmaps == 2:
            c_s.append(np.zeros_like(c_s[0]))

        elif self.n_cmaps == 4:
            c_s = c_s[:3]

        return np.hstack(c_s)
