import os

server_mode = os.getenv("SERVER_MODE", "development")
"""The operational mode of the server."""

stripe_key = os.getenv("STRIPE_API_KEY", None)
"""The stripe API key."""

api_root = "/api/v1"
"""The base url for the api."""

firebase_key_id = os.getenv("FIREBASE_KEY_ID")
"""The firebase API key id."""

firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY")
"""The firebase private key."""
