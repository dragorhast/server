"""
The entry point for the CLI tool
"""

from aiohttp import web

from server import app


def run():
    """Simply runs the imported app."""
    web.run_app(app)


if __name__ == '__main__':
    run()
