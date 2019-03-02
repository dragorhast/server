"""
An abstract class for classes that need to be
rebuilt on startup. Any class that is added to
the app is automatically rebuilt on start.
"""

from abc import ABC, abstractmethod


class Rebuildable(ABC):

    @abstractmethod
    async def _rebuild(self):
        pass
