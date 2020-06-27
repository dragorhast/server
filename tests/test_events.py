import pytest

from server.events import EventHub, NoSuchEventError, NoSuchListenerError, InvalidHandlerError, EventList
from server.events.decorators import emits


class TestException(Exception):
    pass


class ExampleEvents(EventList):

    @staticmethod
    def something_happened(argument):
        """An example event."""


class SecondExampleEvents(EventList):

    @staticmethod
    def something_else_happened(argument):
        """Another event."""


@emits(ExampleEvents, SecondExampleEvents)
class EmittingObject:

    def do_something(self):
        self.emit.something_happened("oops")

    def emit_missing_event(self):
        self.emit.bad_event()


class TestRegistry:

    @staticmethod
    def handler(argument):
        pass

    @staticmethod
    def invalid_handler():
        pass

    async def test_event_list_in_emitter(self):
        """Assert that you can check the existence of an event list on a hub."""
        hub = EventHub(ExampleEvents)
        assert ExampleEvents in hub
        assert SecondExampleEvents not in hub

    async def test_event_in_emitter(self):
        """Assert that you can check the existence of an event on an hub."""
        hub = EventHub(ExampleEvents)
        assert ExampleEvents.something_happened in hub
        assert SecondExampleEvents.something_else_happened not in hub

    async def test_missing_event(self):
        """Assert that getting a non-existent event on an event list raises an error."""
        with pytest.raises(AttributeError):
            ExampleEvents.bad_event

    async def test_event_on_emitter(self):
        """Assert that an event can be accessed through the hub."""
        hub = EventHub(ExampleEvents)
        assert hub.something_happened.event == ExampleEvents.something_happened

    async def test_missing_event_on_emitter(self):
        """Assert that getting a non-existent event on an emitter raises an error."""
        emitter = EventHub()
        with pytest.raises(NoSuchEventError):
            emitter.bad_event

    async def test_subscribe_to_event(self):
        """Assert that a handler can be registered on a hub's event."""
        hub = EventHub(ExampleEvents)
        assert sum((len(l) for l in hub._listeners.values()), 0) == 0
        hub.subscribe(ExampleEvents.something_happened, self.handler)
        assert sum((len(l) for l in hub._listeners.values()), 0) != 0

    async def test_subscriber_has_similar_signature(self):
        """Assert that a subscriber to an event must have a similar signature."""
        emitter = EventHub(ExampleEvents)
        with pytest.raises(InvalidHandlerError):
            emitter.subscribe(ExampleEvents.something_happened, self.invalid_handler)

    async def test_subscribe_to_event_through_emitter(self):
        """Assert that an event can also be referenced through the emitter."""
        emitter = EventHub(ExampleEvents)
        assert sum((len(l) for l in emitter._listeners.values()), 0) == 0
        emitter.subscribe(emitter.something_happened, self.handler)
        assert sum((len(l) for l in emitter._listeners.values()), 0) != 0

    async def test_unsubscribe_from_event(self):
        """Assert that a handler can be unsubscribed from an event."""
        emitter = EventHub(ExampleEvents)
        emitter.subscribe(emitter.something_happened, self.handler)
        emitter.unsubscribe(emitter.something_happened, self.handler)

    async def test_bad_unsubscribe(self):
        """Assert that unsubscribing a handler that isn't registered fails."""
        emitter = EventHub()
        with pytest.raises(NoSuchListenerError):
            emitter.unsubscribe(ExampleEvents.something_happened, self.handler)

    async def test_trigger_event(self):
        emitter = EventHub(ExampleEvents)

        def raise_listener(argument):
            raise TestException("This runs!")

        with pytest.raises(TestException):
            emitter.subscribe(ExampleEvents.something_happened, raise_listener)
            emitter.emit(ExampleEvents.something_happened, argument="test")

    async def test_subscribe_to_event_natural_syntax(self):
        emitter = EventHub(ExampleEvents)
        emitter.something_happened += self.handler

    async def test_unsubscribe_to_event_natural_syntax(self):
        emitter = EventHub(ExampleEvents)
        emitter.subscribe(ExampleEvents.something_happened, self.handler)
        emitter.something_happened -= self.handler

    async def test_trigger_event_natural_syntax(self):
        """Assert that events can be triggered with the natural syntax."""

        def raise_listener(argument):
            raise TestException("This runs!")

        emitter = EventHub(ExampleEvents)
        emitter.something_happened += raise_listener
        with pytest.raises(TestException):
            emitter.something_happened("test")
