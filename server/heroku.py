import os

from server import logger
from server.app import build_app

database_url = os.getenv("DATABASE_URL")

if database_url is not None:
    database_url = database_url.replace("postgres", "postgis", 1)
    database_url = database_url.replace("sqlite", "spatialite", 1)
else:
    logger.error("No database url provided! Exiting.")
    exit(1)

app = build_app(database_url)
