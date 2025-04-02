import sys

if sys.version_info < (3, 8):
    from importlib_metadata import PackageNotFoundError, version
else:
    from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    pass
