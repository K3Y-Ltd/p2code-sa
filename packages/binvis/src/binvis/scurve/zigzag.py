import math

class ZigZag:
    """
    A class representing an n-dimensional zig-zag curve. 
    
    The curve snakes through the n-cube, with each point
    differing from the previous point by exactly one. 
    
    In the 2D example:

    """
    def __init__(self, dimension, size):
        """
        Initializer for the `ZigZag` class.

        Parameters
        ----------
        dimension : int
            The number of dimensions.
        size : int
            The size in each dimension.

        Returns
        -------
        None
            Initializes a `ZigZag` instance.
        """
        self.dimension = int(dimension) 
        self.size = int(size)

    @classmethod
    def fromSize(self, dimension, size):
        """
        Parameters
        ----------
        dimension : int
            The number of dimensions.
        size : int, List[int]
            The size in each dimension.
        """
        x = math.ceil(math.pow(size, 1/float(dimension)))

        if not x**dimension == size:
            raise ValueError("Size does not fit a square ZigZag curve.")
        
        return ZigZag(dimension, int(x))

    def __len__(self):
        return self.size**self.dimension

    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError
        return self.point(idx)

    def dimensions(self):
        """
        Size of this curve in each dimension.
        """
        return [self.size] * self.dimension

    def index(self, p):
        idx = 0
        flip = False
        for power, i in enumerate(reversed(list(p))):
            power = self.dimension-power-1
            if flip:
                fi = self.size-i-1
            else:
                fi = i
            v = fi * (self.size**power)
            idx += v
            if i%2:
                flip = not flip
        return idx

    def point(self, idx):
        """
        Get point with index.
        """
        p = []
        flip = False
        for i in range(self.dimension-1, -1, -1):
            v = idx // (self.size**i)
            if i > 0:
                idx = idx - (self.size**i)*v
            if flip:
                v = self.size-1-v
            p.append(v)
            if v%2:
                flip = not flip
        return reversed(p)
