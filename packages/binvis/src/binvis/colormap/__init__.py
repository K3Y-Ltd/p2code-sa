"""
This module contains colormaps to be applied on a stream
of bytes. Implemented colormaps are the following:
- Byteclass
- Magnitude
- Entropy
- Ordinal (?)
- Detail (?)
"""

from .color_base import DataColorMap
from .color_byte_class import ColorByteClass
from .color_byte_value import ColorByteValue
from .color_byte_entropy import ColorByteEntropy
from .color_mixer import ColorMixer
from .color_mask import ColorMask
from .color_file_structure import ColorTarFileStructure
from .color_block import ColorBlock
