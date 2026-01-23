"""
A `.tar` archive opened with the `tarfile` package returns a 
`tarfile.TarFile` instance which provides an interface to the
tar archive. 

A tar archive is a sequence of blocks. An archive member (a 
stored file) is made up of a header block followed by data blocks. 
Each archive member is represented by a `TarInfo` object.

When we iterate over a `TarFile` instance we get a sequence of
`TarInfo` objects. Each `TarInfo` object has the following 
attributes / methods of interest:

`TarInfo.offset` : int
    The tar header starts here.

`TarInfo.offset_data : int
    The file's data starts here.
    
'0' or (ASCII NUL)	Normal file
'1'	Hard link
'2'	Symbolic link
'3'	Character special
'4'	Block special
'5'	Directory
'6'	FIFO
'7'	Contiguous file
'g'	Global extended header with meta data (POSIX.1-2001)
'x'	Extended header with metadata for the next file in the archive (POSIX.1-2001)
'A'-'Z'	Vendor specific extensions (POSIX.1-1988)
All other values	Reserved for future standardization
"""

from typing import Tuple, Generator
from numpy.typing import ArrayLike

import tarfile
import itertools
import numpy as np

import io

from .iter_color_base import IterableDataColorMap


class IterableColorTarFileStructure(IterableDataColorMap):
    """
    Class to represent a `.tar` file structure as an iterable colormap.

    A `IterableColorTarFileStructure` instance, is a colormap instance
    allowing iteration over chunks of a `.tar` file structure. 
    
    Each file in the `.tar` object starts with a header assigned by the 
    `tar` format followed by the file's content.The `IterableColorTarFileStructure` 
    instance assigns a color the header of each file that represents the file's start
    and a varying color to the file's content based on its
    depth on the tree file structure.
    """

    # Used for header
    TYPE_COLOR_MAP = {
        b"0": 155,
        b"1": 140,
        b"2": 125,
        b"3": 105,
        b"4": 90,
        b"5": 75,
        b"6": 60,
        b"7": 45,
        b"g": 30,
        b"x": 15,
    }

    OTHER_COLOR_MAP = 0

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializer of `IterableColorTarFileStructure` instance.

        For the `IterableColorTarFileStructure` instance, the `iterator`
        attribute holds a `tarfile.Tarfile` instance.

        Parameters
        ----------
        byte_stream : io.BufferedReader
            A buffered reader binary stream.
        size : int
            The total size of the iterator if available.
        """
        super().__init__(*args, **kwargs)

    def _init_iterator(
        self, f: io.BufferedReader, chunk_size: int = 512 * 20
    ) -> Generator:
        """
        A tarfile streamer generator.

        Parameters
        ----------
        f : io.BufferedReader
            A binary file opened with `open(path, 'rb')`
        chunk_size : int
            The iterator chunk size.

        Yields
        ------
        ArrayLike
            An array of color values of length <= `chunk_size` that
            represents the tarfile structure.
        """
        # Initialize tarfile handler `BufferedReader`.
        self.trf_iterator = self._trf_iterator(f)

        # Initialize color map `cycle` per call for reproducibility.
        self.DATA_COLOR_MAP = itertools.cycle([255, 230, 205, 180])

        self._offset, self._color = 0, 0

        cntr = 0

        while True:

            color_array_chunk, ptr = self.create_color_array_chunk(chunk_size)

            if ptr:
                cntr += chunk_size

                if cntr > self.size:
                    yield color_array_chunk[: (chunk_size - (cntr - self.size))]
                else:
                    yield color_array_chunk

            else:
                # This condition means there are remaining file bytes that for
                # some reason were not included in the tarfile iterator. This
                # condition does not comply with the tarfile format but is kept
                # here for check.
                if self.size - cntr > 0:

                    print("Returned bytes are less than the total tarfile bytes.")
                    print("Remaining tarfile bytes will be returned as zeros.")

                    yield np.zeros(self.size - cntr, dtype="uint8")

                self.trf.close()

                return None

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)

    def _trf_iterator(self, f: io.BufferedReader) -> Generator:
        """
        Define generator over tarfile.

        Parameters
        ----------
        f : io.BufferedReader
            A `BufferedReader` instance over a tarfile.

        Yields
        ------
        Tuple[int, int]
            A tuple of (color, size) representing tarfile section.
        """
        self.trf = tarfile.open(fileobj=f, mode="r|")

        for tar_info in self.trf:

            header_clr, header_size, data_clr, data_size = self._parse_trf_info(
                tar_info
            )

            yield header_clr, header_size
            yield data_clr, data_size

    def create_color_array_chunk(self, chunk_size) -> ArrayLike:
        """
        Walk a step of `chunk_size` of the tarfile iterator.

        This function creates a color array of size `chunk_size` by
        iteratively parsing `TarInfo` instances coming from a tarfile
        iterator.

        - For each `TarInfo` instance, based on its header type and its data
        a header color and size and a data color and size are specified.
        - If the array has enough space it is filled with the corresponding
        colors. Else, the 'remaining' header and data are stored in variables
        `self._offsets` and `self._colors` and are used first thing for the
        next array chunk until they are exhausted.

        The color array is represented by a numpy array which is filled inplace.
        To keep track of the position of the array a `ptr` variable is used.
        The `ptr` variable tracks what part of the array remains to be filled
        and is returned along the array.

        NOTE: A tarfile is split into predefined blocks of 512 bytes. For files
        that have smaller size than multiples of 512, the remaining bytes are
        zeros. We will leave these bytes as 0 also.

        Returns
        -------
        clr : ArrayLike
            An array of color values of length `chunk_size`.
        ptr : int
            A pointer indicating the number of array cells that were filled.
        """
        arr = np.zeros(chunk_size, dtype="uint8")

        # A pointer keeps track of the assignment operations on the array
        # if `ptr` == 0 this means that no assignment operation has taken
        # place and is equivalent with returning an empty list
        ptr = 0

        # if we have filled the array or no remaining data exist continue
        if self._offset != 0:

            if (ptr + self._offset) >= chunk_size:

                arr[ptr:] = self._color

                self._offset -= chunk_size - ptr

                # update pointer
                ptr = chunk_size
            else:
                arr[ptr : ptr + self._offset] = self._color

                # update pointer
                ptr = self._update_pointer(ptr + self._offset)

                self._offset = 0

        # Get next (clr, size) section from tarfile iterator until chunk_size
        while ptr < chunk_size:

            try:
                _clr, _size = next(self.trf_iterator)
            except StopIteration:
                break

            if (ptr + _size) >= chunk_size:

                arr[ptr:chunk_size] = _clr

                self._offset = _size - (chunk_size - ptr)
                self._color = _clr

                # update pointer
                ptr = chunk_size
                break

            else:
                arr[ptr : ptr + _size] = _clr

                # update pointer
                ptr = self._update_pointer(ptr + _size)

        return arr, ptr

    def _parse_trf_info(self, tar_info: tarfile.TarInfo) -> Tuple[int, int, int, int]:
        """
        Parse `tar_info` instance.
        """
        header_s = tar_info.offset
        header_e = tar_info.offset_data

        # NOTE: The header's size is usually 512 bytes long, but also
        # extended headers of size 1536 exist.
        header_size = header_e - header_s

        data_size = tar_info.size

        header_clr = self.TYPE_COLOR_MAP.get(tar_info.type, self.OTHER_COLOR_MAP)
        data_clr = next(self.DATA_COLOR_MAP)

        return header_clr, header_size, data_clr, data_size

    def _update_pointer(self, ptr: int) -> int:
        """
        Round pointer to multiples of 512.
        """
        rem = ptr % 512

        return ptr + (512 - rem) if rem else ptr


def test_implementation(path):
    """ """
    import numpy as np

    from binvis.colormap import ColorTarFileStructure
    from binvis.colormap_iter.iter_color_file_structure import (
        IterableColorTarFileStructure,
    )

    CHUNK_SIZE = 512 * 512

    with open(path, "rb") as f:
        byte_array = f.read()

    colormap = ColorTarFileStructure(byte_array)

    colormap_iter = IterableColorTarFileStructure(path, chunk_size=CHUNK_SIZE)

    for i, arr in enumerate(colormap_iter):
        blk = CHUNK_SIZE
        arr1 = colormap.b_arr[blk * i : blk * (i + 1)]

        assert np.all(arr == arr1)
