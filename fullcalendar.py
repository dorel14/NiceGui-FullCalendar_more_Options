
from pathlib import Path
from typing import Any, Optional
from collections.abc import Awaitable, Callable

from nicegui.element import Element
from nicegui.events import handle_event, GenericEventArguments
from nicegui import core, background_tasks
import inspect
class FullCalendar(Element, component='fullcalendar.js'):

    def __init__(self, options: dict[str, Any],
                on_click: Optional[Callable] = None,
                on_dateclick:Optional[Callable] = None,
                on_fetch_events: Optional[Callable] = None) -> None:

        """FullCalendar

        An element that integrates the FullCalendar library (https://fullcalendar.io/) to create an interactive calendar display.

        :param options: dictionary of FullCalendar properties for customization, such as "initialView", "slotMinTime", "slotMaxTime", "allDaySlot", "timeZone", "height", and "events".
        :param on_click: callback that is called when a calendar event is clicked.
        """
        super().__init__()
        self.add_resource(Path(__file__).parent / 'lib')
        self._props['options'] = options
        self._on_fetch_events = on_fetch_events

        if on_click:
            self.on('click', lambda e: handle_event(on_click, e))
        if on_fetch_events:
            self.on('fetch_events', self._handle_fetch_events)

    def add_event(self, title: str, start: str, end: str, **kwargs) -> None:
        """Add an event to the calendar.

        :param title: title of the event
        :param start: start time of the event
        :param end: end time of the event
        """
        event_dict = {'title': title, 'start': start, 'end': end, **kwargs}
        self._props['options']['events'].append(event_dict)
        self.update()
        self.run_method('update_calendar')

    def remove_event(self, title: str, start: str, end: str) -> None:
        """Remove an event from the calendar.

        :param title: title of the event
        :param start: start time of the event
        :param end: end time of the event
        """
        for event in self._props['options']['events']:
            if event['title'] == title and event['start'] == start and event['end'] == end:
                self._props['options']['events'].remove(event)
                break

        self.update()
        self.run_method('update_calendar')

    def _handle_fetch_events(self, e: GenericEventArguments) -> None:
        """Bridge JS → Python : FullCalendar a besoin d'événements."""
        # e.args = {'startStr': ..., 'endStr': ..., 'timeZone': ...}
        handler = self._on_fetch_events

        result = handler(e) if inspect.signature(handler).parameters else handler()

        if isinstance(result, Awaitable):
            # Callback asynchrone → planifié comme tâche en arrière-plan
            background_tasks.create(self._process_fetch_result(result))
        else:
            # Callback synchrone → envoyer immédiatement
            self._send_events(result)

    async def _process_fetch_result(self, result: Awaitable) -> None:
        events = await result
        self._send_events(events)

    def _send_events(self, events: list[dict]) -> None:
        """Bridge Python → JS : envoyer les événements à FullCalendar."""
        self.run_method('provide_events', events)

    @property
    def events(self) -> list[dict[str, Any]]:
        """List of events to display on the calendar."""
        return self._props['options'].get('events', [])
