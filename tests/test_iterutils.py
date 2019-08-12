#coding:utf-8
import pytest
import tempfile
import pathlib
from operator import le, itemgetter, methodcaller
import pandas as pd
import numpy as np
from bourbaki.iterutils import batched, filltail, check_empty_iter, peek, zipcall, do_all
from bourbaki.iterutils.classes import EqualChunks, EqualSlices

n = 10
test_arr = np.arange(n * 3).reshape(n, 3)
test_df = pd.DataFrame(test_arr, columns=["a", "b", "c"])
test_range = range(n)


def compose(*fs):
    # to avoid a toolz/cytoolz dependency for testing
    fs = tuple(reversed(fs))
    def f(x):
        for _ in fs:
            x = _(x)
        return x
    return f


@pytest.fixture(scope="session")
def tempdir():
    temp = pathlib.Path(tempfile.mkdtemp())
    yield temp
    for subdir in temp.iterdir():
        subdir.rmdir()
    temp.rmdir()


@pytest.mark.parametrize("subdirs", [range(10), ["foo", "bar", "baz", "qux"], "abcdefg"])
def test_do_all(tempdir: pathlib.Path, subdirs):
    subdirs = set(map(str, subdirs))
    f = compose(methodcaller("mkdir"), tempdir.__truediv__)
    do_all(map(f, subdirs))

    names = set(p.name for p in tempdir.iterdir())
    assert names == set(subdirs)

    f = methodcaller("rmdir")
    do_all(map(f, tempdir.iterdir()))

    dirs = list(tempdir.iterdir())
    assert not dirs


@pytest.mark.parametrize("size", [3, 5, 7, 10])
@pytest.mark.parametrize("val", [None, "foo", ("b", "a", "r")])
@pytest.mark.parametrize("iterable", [range(3), list("abcd"), np.arange(5), set("foobar"), "abcdefg"])
def test_filltail(size, val, iterable):
    it = iter(filltail(size, val, iterable))
    total = 0
    for x, y in zip(iterable, it):
        assert x == y
        total += 1
    for y in it:
        assert y == val
        total += 1

    assert total == size


def test_zipcall(vals=("asdf", (1, 2, 3, 4), "foo bar baz qux".split(), range(4))):
    fns = map(itemgetter, range(len(vals)))

    for i, val, result in zip(range(len(vals)), vals, zipcall(fns, vals)):
        assert result == val[i]


@pytest.mark.parametrize("iterable", [[], set(), (), [1, 2, 3], "asdf"])
def test_check_empty_iter(iterable):
    it, empty = check_empty_iter(iterable)
    if len(iterable) == 0:
        assert empty
    else:
        assert not empty

    for x, y in zip(it, iterable):
        assert x == y


@pytest.mark.parametrize("iterable", [range(3), list("abcd"), np.arange(5), set("foobar")])
def test_peek(iterable):
    it = iter(iterable)
    first, all_ = peek(it)

    # fresh copy of iterator state
    it_ = iter(iterable)
    assert next(it_) == first
    # peel off first from peeked iterator
    next(all_)

    for x, y in zip(it_, all_):
        assert x == y


def flatiter(coll):
    if isinstance(coll, pd.DataFrame):
        return coll.values.flatten()
    if isinstance(coll, np.ndarray):
        return coll.flatten()
    return coll


@pytest.mark.parametrize("iterable", [test_arr, test_df, test_range])
@pytest.mark.parametrize("size", [1, 2, 3, 4, 5])
def test_batched(iterable, size):
    nchunks, rem = divmod(len(iterable), size)
    nchunks += int(bool(rem))
    rem = rem or size
    type_ = type(iterable)
    i = None

    for i, chunk in enumerate(batched(iterable, size), 1):
        size_ = rem if i == nchunks else size
        assert isinstance(chunk, type_)
        assert len(chunk) == size_
        flat = flatiter(chunk)
        assert all(x == y for x, y in zip(flat, range(flat[0], flat[-1] + 1)))

    assert i == nchunks


def listrange(n):
    return list(range(n))


@pytest.mark.parametrize("cls", [EqualChunks, EqualSlices])
@pytest.mark.parametrize("type_", [range, listrange])
@pytest.mark.parametrize("size", list(range(0, 15, 4)))
@pytest.mark.parametrize("n", list(range(0, 30, 7)))
def test_EqualChunks_EqualSlices_with_size(n, size, type_, cls):
    kw = dict(targetsize=size)
    if size == 0:
        with pytest.raises(ValueError):
            o = cls(type_(n), **kw)
    else:
        o = cls(type_(n), **kw)
        assert len(o) == len(list(o))

        if len(o) == 0:
            assert o.small is None and o.big is None
        else:
            assert o.big - o.small <= 1
            assert o.small * o.numsmall + o.big * o.numbig == len(type_(n))
            assert sum(map(len, o)) == n

            if size > n:
                assert o.small == n and o.big == n
            else:
                low = n // ((n // size) + 1) if le(*divmod(n, size)) else size - 1
                assert o.small >= low and o.big <= size


@pytest.mark.parametrize("cls", [EqualChunks, EqualSlices])
@pytest.mark.parametrize("type_", [range, listrange])
@pytest.mark.parametrize("nchunks", list(range(0, 15, 4)))
@pytest.mark.parametrize("n", list(range(0, 30, 7)))
def test_EqualChunks_EqualSlices_with_nchunks(n, nchunks, type_, cls):
    kw = dict(nchunks=nchunks)
    if nchunks == 0 and n != 0:
        with pytest.raises(ValueError):
            o = cls(type_(n), **kw)
    else:
        o = cls(type_(n), **kw)
        assert len(o) == len(list(o))

        if len(o) == 0:
            assert o.small is None and o.big is None
        else:
            assert o.big - o.small <= 1
            assert o.small * o.numsmall + o.big * o.numbig == len(type_(n))
            assert sum(map(len, o)) == n

            if nchunks > n:
                assert o.small == 1 and o.big == 1
                assert o.numsmall == n and o.numbig == 0
            else:
                size = n // nchunks
                assert o.small >= size - 1 and o.big <= size + 1
