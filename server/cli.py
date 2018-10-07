"""
The entry point for the CLI tool
"""

from aiohttp import web

from server import APP


def run():
    """Simply runs the imported app."""
    web.run_app(APP)


if __name__ == '__main__':
    run()
