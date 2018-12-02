"""
The main package for the API server.
"""

import logging
import os

from server.store.persistent_store import PersistentStore
from .store import Store

server_mode = os.getenv("SERVER_MODE", "development")

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG if server_mode == "development" else logging.INFO)

store: PersistentStore = Store()

api_root = "/api/v1"
"""The base url for the api."""

