import numpy as np


class DataColorMap:
    """
    Class to represent a base data colormap object.

    A `DataColorMap` instance is initialized given an
    iterable of integers where each integer corresponds
    to a byte value.

    Each subclass of the `DataColorMap` class implements
    the `.get_point` method, which given an index on the
    domain of the data array, returns a color value.
    """

    def __init__(self, data):
        """
        Initializer of `DataColorMap` instance.

        Parameters
        ----------
        data : bytes
            Input data in binary format.
        """
        self._validate_input(data)
        
        self.data = data
        self.b_arr = np.frombuffer(data, dtype="uint8")

    def __len__(self):
        return len(self.data)

    def _validate_input(self, data):
        """
        Validate input.
        """
        if not isinstance(data, bytes):
            raise ValueError("Input must be a bytearray.")

    def get_shape(self):
        return self.b_arr.shape

    def get_point(self, idx, mode="L"):
        """
        Return color for given byte-array index.
        """
        c = int(self.data[idx])

        if mode == "RGB":
            return (c, c, c)

        elif mode == "L":
            return c

    def get_point_np(self, idx, mode="L"):
        """
        Return color for given index. Support `int`, `slice`, `array`

        Parameters
        ----------
        idx : Union[int, slice, ArrayLike]
            Index to get value of stored byte-array in `self.data`.
        mode : {'RGB', 'L'}
            The shape and format of output colors.
        """
        b_arr = self.b_arr[idx]

        if isinstance(idx, int):
            b_arr = b_arr.reshape(1, 1)

        elif isinstance(idx, slice) or isinstance(idx, np.ndarray):
            b_arr = b_arr[:, np.newaxis]

        else:
            raise ValueError(
                (
                    "`idx` argument must be either of type `int`, `slice` "
                    "or and indexing numpy array."
                )
            )

        if mode == "RGB":
            return np.tile(b_arr, 3)

        elif mode == "L":
            return b_arr

    @classmethod
    def from_file(cls, file):
        """
        Create a `DataColorMap` instance directly from file.
        """
        with open(file, "rb") as f:
            data = f.read()

        return cls(data=data)
