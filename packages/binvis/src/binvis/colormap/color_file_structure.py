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
'A'–'Z'	Vendor specific extensions (POSIX.1-1988)
All other values	Reserved for future standardization
"""

import io
import tarfile
import itertools
import numpy as np

from .color_base import DataColorMap


class ColorTarFileStructure(DataColorMap):
    """
    Class to represent a `.tar` file structure as a colormap.

    A `ColorTarFileStructure instance, returns a colormap
    representation of a `.tar` file structure.  Each file in
    the `.tar` object starts with a header assigned by the
    `tar` format followed by the file's content.

    The `ColorTarFileStructure` instance assigns a color for
    the header of each file that represents the file's start
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

    def __init__(self, data):
        """
        Initializer of `ColorTarFileStructure` instance.

        Parameters
        ----------
        data : bytes
            Input data in binary format.
        """
        self._validate_input(data)

        self.data = self.tarfile_to_color(data)
        self.b_arr = np.frombuffer(self.data, dtype="uint8")

    def tarfile_to_color(self, data):
        """
        Convert `.tar` file to 1-channel color values.
        """
        # Initialize color map `cycle` per call for reproducibility.
        DATA_COLOR_MAP = itertools.cycle([255, 230, 205, 180])

        clr = bytearray(len(data))

        try:
            b = io.BytesIO(data)

            with tarfile.open(fileobj=b) as trf:

                for tar_info in trf:

                    header_s = tar_info.offset
                    header_e = tar_info.offset_data
                    # NOTE: Is the header's size always 512 bytes?
                    header_size = header_e - header_s

                    data_s = tar_info.offset_data
                    data_e = tar_info.offset_data + tar_info.size
                    data_size = tar_info.size

                    slc_header = slice(header_s, header_e)
                    slc_data = slice(data_s, data_e)

                    clr_header = self.TYPE_COLOR_MAP.get(
                        tar_info.type, self.OTHER_COLOR_MAP
                    )
                    clr_data = next(DATA_COLOR_MAP)

                    clr[slc_header] = [clr_header] * header_size
                    clr[slc_data] = [clr_data] * data_size

        except Exception:
            raise ValueError()
        finally:
            b.close()

        return bytes(clr)

    def _validate_input(self, data):
        """
        Validate input.
        """
        super()._validate_input(data)

        with io.BytesIO(data) as b:
            if not tarfile.is_tarfile(b):
                raise ValueError(
                    "Input `bytes` instance does not represent a `tarfile`"
                )
