from collections import defaultdict
from inspect import signature, iscoroutinefunction, Signature
from typing import Type, Union, Callable, List, Dict

from .event_emitter import EventEmitter, AsyncEventEmitter
from .event_list import EventList, AsyncEventList
from .exceptions import NoSuchEventError, InvalidHandlerError, NoSuchListenerError


class EventHub:
    """An emitter. This is added to an object and maintains all the events it can emit."""

    def __init__(self, *events: Type[EventList]):
        self._event_lists = events
        self._listeners: Dict[Callable, List[Callable]] = defaultdict(list)

    def add_events(self, *events):
        if any(not issubclass(e, EventList) for e in events):
            raise TypeError("All events must be of type EventList!")
        self._event_lists += events

    def emit(self, target: Union[Callable, EventEmitter], *args, **kwargs):
        event = self._resolve_event(target)
        for handler in self._listeners[event]:
            handler(*args, **kwargs)

    def __contains__(self, item):
        """Checks if the emitter emits the given event."""
        if isinstance(item, type) and issubclass(item, EventList):
            return item in self._event_lists
        return any(item in event_list for event_list in self._event_lists)

    def __getattr__(self, item: str):
        """Intercepts getattribute and raises if the event does not exist."""
        for event_list in self._event_lists:
            try:
                event = getattr(event_list, item)
            except NoSuchEventError:
                pass
            else:
                return EventEmitter(self, event)
        raise NoSuchEventError()

    def subscribe(self, target: Union[Callable, EventEmitter], handler: Callable):
        """
        :param target: The event to listen for.
        :param handler: The event handler.
        """
        event = self._resolve_event(target)
        if event not in self:
            raise NoSuchEventError("Event does not exist on the given target.")

        event_keys = [x for x in signature(event).parameters.items() if not x[0] == "self"]
        handler_keys = [x for x in signature(handler).parameters.items() if not x[0] == "self"]

        errors = []
        if not len(event_keys) == len(handler_keys):
            errors.append(InvalidHandlerError("Parameters are of conflicting lengths.", target, handler))

        for (e_name, e_param), (h_name, h_param) in zip(event_keys, handler_keys):
            if not e_name == h_name:
                errors.append(InvalidHandlerError("Parameters do not match.", e_name, h_name))

            if e_param.annotation is not Signature.empty and h_param.annotation is not Signature.empty:
                if e_param.annotation is not h_param.annotation:
                    errors.append(
                        InvalidHandlerError(f"Conflicting annotations for parameter \"{e_name}\".", target, handler))

        if errors:
            raise InvalidHandlerError(errors)

        self._listeners[event].append(handler)

    def unsubscribe(self, target: Union[Callable, EventEmitter], handler: Callable):
        event = self._resolve_event(target)
        try:
            self._listeners[event].remove(handler)
        except ValueError:
            raise NoSuchListenerError("%s not currently registered", handler)

    @staticmethod
    def _resolve_event(target: Union[Callable, EventEmitter]) -> Callable:
        if isinstance(target, EventEmitter):
            event = target.event
        else:
            event = target
        return event


class AsyncEventHub(EventHub):

    def __init__(self, *events: Union[Type[EventList], Type[AsyncEventList]]):
        super().__init__(*events)
        self._async_listeners: Dict[Callable, List[Callable]] = defaultdict(list)

    async def emit(self, target: Union[Callable, EventEmitter], *args, **kwargs):
        event = self._resolve_event(target)
        super().emit(event, *args, **kwargs)
        for handler in self._async_listeners[event]:
            await handler(*args, **kwargs)

    def subscribe(self, target: Union[Callable, EventEmitter], handler: Callable):
        """
        :param target: The event to listen for.
        :param handler: The event handler.
        """
        event = self._resolve_event(target)
        if event not in self:
            raise NoSuchEventError("Event does not exist on the given target.")

        event_keys = signature(event).parameters.keys()
        handler_keys = signature(handler).parameters.keys()

        if not event_keys == handler_keys:
            raise InvalidHandlerError(
                "Handler signature does not match.",
                event_keys, handler_keys
            )
        if iscoroutinefunction(handler):
            self._async_listeners[event].append(handler)
        else:
            self._listeners[event].append(handler)

    def unsubscribe(self, target: Union[Callable, EventEmitter], handler: Callable):
        event = self._resolve_event(target)
        try:
            if iscoroutinefunction(handler):
                self._async_listeners[event].remove(handler)
            else:
                self._listeners[event].remove(handler)
        except ValueError:
            raise NoSuchListenerError("%s not currently registered", handler)

    def __getattr__(self, item: str):
        """Intercepts getattribute and raises if the event does not exist."""
        for event_list in self._event_lists:
            try:
                event = getattr(event_list, item)
            except NoSuchEventError:
                pass
            else:
                if issubclass(event_list, AsyncEventList):
                    return AsyncEventEmitter(self, event)
                else:
                    return EventEmitter(self, event)
        raise NoSuchEventError()
