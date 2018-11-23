from .memory import MemoryStore
from .postgres import PostgresStore

USE_MEMORY = True

Store = MemoryStore if USE_MEMORY else PostgresStore
