from typing import Generator

import io
import os

import numpy as np


class IterableDataColorMap:
    """
    Class to represent a base `IterableDataColorMap` object that can 
    be iterated over.

    A `IterableDataColorMap` instance is initialized given a path to 
    a file, aimed to be converted to a color map. The `IterableDataColorMap`
    can then be iterated over in chunks where the input file is sequentially
    loaded into memory and returned as a numpy array until exhaustion.
    
    Example
    -------
    >>> path = "path-to-file"
    >>> cmap = IterableDataColorMap(path=path)
    >>> for chunk in cmap:
    >>>    print(len(chunk))
    """

    def __init__(self, path: str, chunk_size: int = 20 * 512) -> None:
        """
        Initializer of `IterableDataColorMap` instance.

        Parameters
        ----------
        path : str
            A path to binary file to iterate over.
        chunk_size : int
            The iterator maximum chunk size.
        """
        self.f = open(path, "rb")
        self.size = os.path.getsize(path)

        self.chunk_size = chunk_size
        self.iterator = self._init_iterator(self.f, self.chunk_size)

    def __len__(self):
        """
        Return file total size.
        """
        return self.size

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)

    def close(self) -> None:
        """
        Close `io.BufferedReader` and `Iterator` instance.
        """
        if hasattr(self.f, "close"):
            self.f.close()

        if hasattr(self.iterator, "close"):
            self.iterator.close()

    def _init_iterator(
        self, f: io.BufferedReader, chunk_size: int = 512 * 20
    ) -> Generator:
        """
        A byte streamer generator.

        Parameters
        ----------
        f : io.BufferedReader
            A binary file opened with `open(path, 'rb')`
        chunk_size : int
            The iterator maximum chunk size.

        Yields
        ------
        bytearray
            A chunk of bytes.
        """
        if f.closed is True:
            return

        while True:
            chunk = f.read(chunk_size)

            if chunk:
                yield np.frombuffer(chunk, dtype="uint8")
            else:
                return
