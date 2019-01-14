import os

server_mode = os.getenv("SERVER_MODE", "development")
"""The operational mode of the server."""

api_root = "/api/v1"
"""The base url for the api."""
