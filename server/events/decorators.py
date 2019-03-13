from typing import Type

from .event_hub import EventHub
from .event_list import EventList


def emits(*possible_events: Type[EventList]):
    """A simple decorator that, when added to a class, wires up an emitter for it with the given event lists."""

    def class_decorator(cls: Type):

        if hasattr(cls, "hub"):
            cls.hub.add_events(*possible_events)
        else:
            cls.hub = EventHub(*possible_events)

        return cls

    return class_decorator
