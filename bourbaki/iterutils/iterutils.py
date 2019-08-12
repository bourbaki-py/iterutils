# coding:utf-8
from itertools import chain, islice, repeat
from .classes import Slices, Chunks, EqualChunks, EqualSlices, is_sliceable


# small iterable helpers

def batched(seq, batch_size=None):
    if is_sliceable(seq):
        return Slices(seq, batch_size)
    return Chunks(seq, batch_size)


def even_batched(seq, size=None, nchunks=None, len_=None):
    if is_sliceable(seq):
        return EqualSlices(seq, targetsize=size, nchunks=nchunks, len_=len_)
    return EqualChunks(seq, targetsize=size, nchunks=nchunks, len_=len_)


def do_all(map_):
    """force evaluation of an iteration with side effects; e.g. `do_all(map(print, my_iterable))`.
    Saves a loop that would otherwise be necessitated by the lazyness of some iterator-combinators like `map`"""
    for _ in map_:
        try:
            p = _.absolute()
        except Exception:
            p = None
        print(_, p, type(_))
        pass


def peek(iterable):
    first = next(iterable)
    return first, chain((first,), iterable)


def filltail(n: int, v, iterable):
    return islice(chain(iterable, repeat(v)), n)


def zipcall(fns, vals):
    return (f(v) for f, v in zip(fns, vals))


def check_empty_iter(iterable):
    iterator = iter(iterable)
    try:
        x = next(iterator)
    except StopIteration:
        empty = True
    else:
        empty = False
        iterator = chain((x,), iterator)

    return iterator, empty
