# coding:utf-8
from typing import Mapping, MappingView
from abc import ABC
from warnings import warn
from itertools import islice
from functools import singledispatch
import numpy as np
import pandas as pd


# ABC for common int-range sliceable objects

class Sliceable(ABC):
    @classmethod
    def __subclasshook__(cls, subclass):
        if not hasattr(subclass, '__getitem__') or not callable(subclass.__getitem__):
            return False

        if issubclass(cls, (Mapping, MappingView, pd.DataFrame, pd.Series)):
            return False

        return True

    def __getitem__(self, item):
        pass


for cls in (list, tuple, str, range, bytes, np.ndarray, pd.Index, pd.core.indexing._iLocIndexer):
    Sliceable.register(cls)


def is_sliceable(obj):
    return isinstance(obj, Sliceable)


class NotSliceableError(TypeError):
    def __init__(self, t):
        self.args = (t,)

    def __str__(self):
        return "object of type {} is not efficiently sliceable".format(self.args[0])


@singledispatch
def to_sliceable(obj):
    raise NotSliceableError(type(obj))


@to_sliceable.register(Sliceable)
def to_sliceable_sliceable(obj):
    return obj


def to_sliceable_pandas(obj):
    return obj.iloc


for pdtype in (pd.Series, pd.DataFrame):
    to_sliceable.register(pdtype)(to_sliceable_pandas)


# batching iterables

class Chunks:
    def __init__(self, iterable, size):
        self.iterable = iterable
        self.iterator = None
        self.size = size

    def __iter__(self):
        self.iterator = iter(self.iterable)
        return self

    def __next__(self):
        chunk = list(islice(self.iterator, self.size))
        if not chunk:
            raise StopIteration()
        return chunk


class Slices(Chunks):
    def __init__(self, sliceable, size):
        # this will ensure a sliceable type
        self.sliceable = to_sliceable(sliceable)
        super().__init__(sliceable, size)
        len_ = len(sliceable)
        nchunks, rem = divmod(len_, size)
        self.len_ = len_
        self.nchunks = nchunks + int(bool(rem))

    def __iter__(self):
        self.i = 0
        self.n = 0
        return self

    def __next__(self):
        if self.i >= self.nchunks:
            raise StopIteration()

        chunk = self.sliceable[self.n:(self.n + self.size)]
        self.i += 1
        self.n += self.size
        return chunk

    def __len__(self):
        return self.nchunks


class EqualChunks:
    def __init__(self, iterable, *, targetsize=None, nchunks=None, len_=None):
        # find length of iterable
        if len_ is not None and (not isinstance(len_, int) or len_ <= 0):
            raise TypeError("If you pass the len_ keyword arg manually, it must be a positive int")
        else:
            try:
                len_ = len(iterable)
            except TypeError:
                TypeError("Iterable of type {} has no len(); "
                          "you must pass a positive int to the len_ keyword arg".format(type(iterable)))

        # check the input chunk size specs
        valerror = ValueError("must pass a positive int for only one of nchunks, size")
        if targetsize is not None and nchunks is not None:
            raise valerror
        elif targetsize is not None:
            if not isinstance(targetsize, int) or targetsize <= 0:
                raise valerror
            n, rem = divmod(len_, targetsize)
            nchunks = n + int(bool(rem))
        elif nchunks is not None:
            if not isinstance(nchunks, int):
                if nchunks < 0 or (nchunks == 0 and len_ != 0):
                    raise valerror
            nchunks = min(len_, nchunks)
        else:
            raise valerror

        self.len_ = len_

        # determine big, small, nchunks
        if nchunks == 0:
            if len_ != 0:
                raise ValueError("arguments len_ is {} but nchunks={} was passed".format(len_, nchunks))
            self.small, self.big = None, None
            self.numsmall, self.numbig = 0, 0
        else:
            # distribute 1's to the smalls from the remainder
            small, numbig = divmod(len_, nchunks)
            if targetsize is not None and small > targetsize:
                nchunks += 1
                small, numbig = divmod(len_, nchunks)

            big = small + int(bool(len_ % small)) if small != 0 else 1
            numsmall = (len_ - numbig * big) // small

            self.small, self.big = small, big
            self.numsmall, self.numbig = numsmall, numbig

        self.nchunks = nchunks
        self.iterable = iterable
        self.iterator = None
        self.i = None

    def __iter__(self):
        self.iterator = iter(self.iterable)
        self.i = 0
        return self

    def __next__(self):
        if self.i < self.nchunks:
            size = (self.small + 1) if self.i < self.numbig else self.small
            result = list(islice(self.iterator, size))
        else:
            raise StopIteration()
        self.i += 1
        return result

    def __len__(self):
        return self.nchunks


class EqualSlices(EqualChunks):
    def __init__(self, sliceable, *, targetsize=None, nchunks=None, len_=None):
        # this will ensure a sliceable type
        self.sliceable = to_sliceable(sliceable)
        super().__init__(sliceable, targetsize=targetsize, nchunks=nchunks, len_=len_)

    def __iter__(self):
        self.i = 0
        self.n = 0
        return self

    def __next__(self):
        if self.i < self.nchunks:
            size = (self.small + 1) if self.i < self.numbig else self.small
            result = self.sliceable[self.n:(self.n + size)]
            if len(result) != size:
                warn("chunk size is specified as {} but got slice of len {}; perhaps len_ was incorrect at init?"
                     .format(size, len(result)))
        else:
            raise StopIteration()
        self.i += 1
        self.n += size
        return result
