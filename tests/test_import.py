import os
import pytest
from pathlib import Path
from setuptools.config import read_configuration
namespace = 'bourbaki'
pardir = Path(__file__).parent.parent
modname = next(f.name for f in (pardir / namespace).iterdir() if f.is_dir() and f.name != '__pycache__')


@pytest.fixture(scope='module')
def pkgname_from_dirs():
    return '{}.{}'.format(namespace, modname)


@pytest.fixture(scope='module')
def pkgname_from_config():
    conf = read_configuration(os.path.join(pardir, 'setup.cfg'))
    return conf['metadata']['name']


def test_import(pkgname_from_dirs):
    """
    This test demonstrates the use of a _fixture_. It's not super useful in this case, but in general if you have
    tests that depend on some mutable state that you want to reinitialize each time, or some object that is immutable
    but expensive to instantiate, or a connection to a database, file, or other I/O, this is a good way to do it.
    The argument name 'pkgname_from_dirs' here tells pytest to call the above function with the same name, and pass
    that value in for the argument's value. With the scope='module' specification up there we're telling pytest it only
    needs to evaluate that fixture once for the duration of this test suite."""
    print(pkgname_from_dirs)
    __import__(pkgname_from_dirs)


def test_import_from_config(pkgname_from_config):
    __import__(pkgname_from_config)


def test_equal_pkgnames(pkgname_from_dirs, pkgname_from_config):
    assert pkgname_from_dirs == pkgname_from_config
