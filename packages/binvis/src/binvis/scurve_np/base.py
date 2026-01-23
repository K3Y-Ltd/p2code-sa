class CurveBase:
    """
    Class to represent an n-dimensional box space-filling curve.
    """

    def __init__(self, size: int, dimension: int = 2) -> None:
        """
        Initializer for the `CurveBase` class.

        Parameters
        ----------
        dimension : int
            The number of dimensions.
        size : int
            The size in each dimension.

        Returns
        -------
        None
            Initializes a `CurveBase` instance.
        """
        self._validate_args(size, dimension)

        self.dimension = int(dimension)
        self.size = int(size)

    def _validate_args(self, size: int, dimension: int) -> None:
        """
        Validate dimension and size to fit a square curve.
        """
        if dimension != int(dimension):
            raise ValueError("`dimension` must be an integer.")

        if size != int(size):
            raise ValueError("`size` must be an integer.")

    def __len__(self) -> int:
        return self.size**self.dimension
