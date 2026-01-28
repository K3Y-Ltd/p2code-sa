from io import BufferedReader
from typing import List, Tuple, Generator

import itertools

import numpy as np

from .iter_color_base import IterableDataColorMap


class IterableColorMask(IterableDataColorMap):
    """
    Class to represent a colormap object that creates a color
    mask on blocks specified by index spans.

    The `ColorMask` instance does not require a byte buffer to
    be initialized as other classes of the `colromap` module,
    but a list of spans and the total length on blocks specified
    by index spans.
    """

    MASK_COLOR = 255

    def __init__(
        self, size: int, spans: List[Tuple[int, int]], chunk_size: int = 20 * 512
    ) -> None:
        """
        Initializer for the `IterableColorMask` instance.
        """
        self.size = size
        self.chunk_size = chunk_size
        self.spans = spans

        self.iterator = self._init_iterator(self.spans, self.chunk_size)

    def _init_iterator(
        self, spans: List[Tuple[int, int]], chunk_size: int = 512 * 20
    ) -> Generator:
        """
        Initialize iterator.
        """
        self.span_iter = (span for span in spans)

        chunk_idx = [idx for idx in range(0, self.size, chunk_size)] + [self.size]

        chunk_iter = itertools.pairwise(chunk_idx)

        s_arr, e_arr = next(chunk_iter)
        s_spn, e_spn = next(self.span_iter)

        new_arr = True

        while True:

            if new_arr is True:
                arr = np.zeros((e_arr - s_arr, 3), dtype="uint8")

            # 1. array span is behind the mask span
            if s_spn >= e_arr:

                # if array span is behind the mask span (no overlap)
                # return color array and walk the chunk iterator
                yield arr

                new_arr = True

                try:
                    s_arr, e_arr = next(chunk_iter)
                except StopIteration:
                    break

            # 2. mask span start lies between the array span endpoints &
            #    mask span end also lies between array span endpoints

            # if the mask span lies between the array span build color
            # array with mask indices changed. Walk chunk iterator.
            elif (s_spn >= s_arr and s_spn < e_arr) and e_spn < e_arr:

                arr[s_spn % chunk_size : e_spn % chunk_size, :] = self.MASK_COLOR

                new_arr = False

                try:
                    s_spn, e_spn = next(self.span_iter)
                except StopIteration:
                    break

            # 3. mask span start lies between the array span endpoints but
            #    mask span end lies outside array span endpoints

            # if the mask span has partial overlap with the array span, we
            # return color array with overlapping mask indices changed. Walk
            # chunk iterator and update mask span.

            # There shouldnt exist a mask that is beyond the final span.
            elif (s_spn >= s_arr and s_spn < e_arr) and e_spn >= e_arr:

                arr[s_spn % chunk_size :, :] = self.MASK_COLOR

                # update mask span
                s_spn = e_arr

                yield arr

                new_arr = True

                try:
                    s_arr, e_arr = next(chunk_iter)
                except StopIteration:
                    print("Not valid mask?")
                    break

            # 4. array span is in front of the mask span
            elif s_arr > e_spn:

                # if array span is in front of the mask span (no overlap)
                # simply walk the mask span iterator. there is no other
                # mask span, return current color array and break while loop
                try:
                    s_spn, e_spn = next(self.span_iter)
                except StopIteration:
                    break

        if new_arr is False:
            yield arr

        # Return remaining chunks
        for s_arr, e_arr in chunk_iter:
            yield np.zeros((e_arr - s_arr, 3), dtype="uint8")

    def close(self) -> None:
        """
        Close `BufferedReader` and `Iterator` instance.
        """
        if hasattr(self.iterator, "close"):
            self.iterator.close()
