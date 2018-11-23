"""
Handles all the persistence for the application.
Currently has two implementations: in-memory and
postgres databases.
"""

from .memory import MemoryStore
from .postgres import PostgresStore

USE_MEMORY = True

Store = MemoryStore if USE_MEMORY else PostgresStore
