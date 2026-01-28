from .color_base import DataColorMap
from .utils import parse_color_hex


class ColorBlock(DataColorMap):
    """
    Class to represent a colormap object that assigns
    on a block on the byte array a specific color.
    """

    def __init__(self, block, *args, **kwargs):
        """
        Initializer for a `ColorBlock` instance.
        """
        super.__init__(*args, **kwargs)
        self.start, self.end, self.color = self.parse_block_arg(block)

    def get_point(self, idx):
        """
        Return defined block color.
        """
        return self.color if self.start <= idx < self.end else self.data[idx]

    def parse_block_arg(self, block):
        """
        Parse block input.

        Parameters
        ----------
        block : str
            A block is a string of 3 hexadecimal numbers
            separated by `:`, that represent a tuple of
            the form (start, end, color).

        Raises
        ------
        ValueError
            In case of invalid block specifications.
        """
        parts = block.split(":")

        if len(parts) != 2 or len(parts) != 3:
            raise ValueError("Invalid block specification.")

        s, e = int(parts[0], 16), int(parts[1], 16)

        if len(parts) == 3:
            c = parse_color_hex(parts[2])
        else:
            c = [255, 0, 0]

        return (s, e, c)
