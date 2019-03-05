import os

server_mode = os.getenv("SERVER_MODE", "development")
"""The operational mode of the server."""

stripe_key = os.getenv("STRIPE_API_KEY", None)
"""The stripe API key."""

api_root = "/api/v1"
"""The base url for the api."""
