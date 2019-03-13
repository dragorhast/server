"""
.. autoclasstree:: server.events

This module provides a simple event system. It is centered around the use of hubs.
A hub is created by passing a number of event lists in. These event lists provide
typed callback signatures which subscribers can use to implement their handlers.

>>> class WeatherEvents(EventList):
>>>     @staticmethod
>>>     def this_happened(name: str):
>>>         "Something important has happened."
>>>
>>> def weather_handler(name):
>>>     print(f"New weather: {name}")
>>>
>>> hub = EventHub(WeatherEvents)
>>> hub.subscribe(WeatherEvents.this_happened, weather_handler)
>>> hub.emit(WeatherEvents.this_happened, "It is raining.")
New weather: It is raining.

Hubs can be also be globally attached to classes with a decorator.
"""

from .event_hub import EventHub, AsyncEventHub
from .event_list import EventList, AsyncEventList
from .exceptions import NoSuchEventError, NoSuchListenerError, InvalidHandlerError
