from typing import Callable

from server.events.exceptions import NoSuchEventError


class EventListMeta(type):

    def __contains__(self, event: Callable):
        """Checks if the event (by name) exists on the events list."""
        event_name = event.__name__
        try:
            return event is getattr(self, event_name)
        except NoSuchEventError:
            return False

    # def __getattr__(self, item):
    #     """
    #     Intercepts getattribute and raises if the event does not exist.
    #
    #     .. note:: Python checks for the existence of `_subs_tree` which will fail
    #         so we need to ignore in that case.
    #     """
    #     if item not in ("_subs_tree",):
    #         raise NoSuchEventError(item)
    #     else:
    #         super().__getattr__(item)


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
