from torch.utils.data.datapipes.datapipe import IterDataPipe
from torch.utils.data.datapipes.utils.common import _check_unpickable_fn


class FlatMapperIterDataPipe(IterDataPipe):
    """
    A class to represent a `FlatMapperIterDataPipe`.

    An iterable DataPipe which applies a structure-changing function to
    an IterableDataPipe flattens to a single unnested IterableDataPipe.

    Parameters
    ----------
    datapipe : IterDataPipe
        Iterable datapipe containing iterable datapipes to which the
        function is applied.

    fn : Callable
        The function to be applied to each of the "inner" datapipes.
    """

    def __init__(self, datapipe, fn):
        self.datapipe = datapipe

        _check_unpickable_fn(fn)
        self.fn = fn  # type: ignore[assignment]

    def __iter__(self):
        for e in self.datapipe:
            yield from self.fn(e)

    def __len__(self):
        raise TypeError(
            f"{type(self).__name__}'s length relies on the output of its function."
        )

    def __getstate__(self):
        if IterDataPipe.getstate_hook is not None:
            return IterDataPipe.getstate_hook(self)

        dill_function = self.fn

        state = (
            self.datapipe,
            dill_function,
        )
        return state

    def __setstate__(self, state):
        (
            self.datapipe,
            dill_function,
        ) = state

        self.fn = dill_function  # type: ignore[assignment]
