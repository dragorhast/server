"""
Version
-------

Defines the version of the application.

.. autodata:: server.version.__version__
"""

__version__ = "1.0.0"
"""The current version."""

short_version = ".".join(__version__.split(".")[:2])
"""A short version."""

name = "tap2go-server"
