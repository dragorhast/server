from typing import Callable

from server.events.exceptions import NoSuchEventError


class EventListMeta(type):

    def __contains__(self, event: Callable):
        """Checks if the event (by name) exists on the events list."""
        event_name = event.__name__
        try:
            return event is getattr(self, event_name)
        except AttributeError:
            return False


class EventList(metaclass=EventListMeta):
    """
    Contains a list of emittable events.
    Events are defined as functions on a subclass
    of the EventList type, and their signatures
    used to determine the "contract" of the event.
    """


class AsyncEventList(EventList):
    """
    Signifies a list of async events.
    """
