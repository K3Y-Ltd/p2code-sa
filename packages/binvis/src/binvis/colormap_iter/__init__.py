"""
This module contains colormaps to be applied on a stream
of bytes. Implemented colormaps are the following:
- Byteclass
- Magnitude
- Entropy
- Ordinal (?)
- Detail (?)
"""

from .iter_color_base import IterableDataColorMap
from .iter_color_byte_class import IterableColorByteClass
from .iter_color_byte_value import IterableColorByteValue
from .iter_color_file_structure import IterableColorTarFileStructure
from .iter_color_mixer import IterableColorMixer
from .iter_color_mask import IterableColorMask
