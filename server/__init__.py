"""
The main package for the API server.
"""

import logging
from .store import Store

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

Store = Store()

api_root = "/api/v1"
"""The base url for the api."""
