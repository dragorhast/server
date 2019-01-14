import os

from server.app import build_app

database_url = os.getenv("DATABASE_URL", None)

app = build_app(database_url)
