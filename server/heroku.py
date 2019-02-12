import os

from server.app import build_app

database_url = os.getenv("DATABASE_URL", None).replace("postgres", "postgis", 1)

app = build_app(database_url)
