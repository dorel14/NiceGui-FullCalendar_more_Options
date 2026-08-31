from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from nicegui import background_tasks
from nicegui.element import Element
from nicegui.events import GenericEventArguments, handle_event


class FullCalendar(Element, component="fullcalendar_comp.js"):
    def __init__(
        self,
        options: dict[str, Any],
        on_click: Callable | None = None,
        on_dateclick: Callable | None = None,
        on_fetch_events: Callable | None = None,
    ) -> None:
        """FullCalendar

        An element that integrates the FullCalendar library (https://fullcalendar.io/) to create an interactive calendar display.

        :param options: dictionary of FullCalendar properties for customization, such as "initialView", "slotMinTime", "slotMaxTime", "allDaySlot", "timeZone", "height", and "events".
        :param on_click: callback that is called when a calendar event is clicked.
        """
        super().__init__()
        self.add_resource(Path(__file__).parent / "lib")
        self._props["options"] = options
        self._on_fetch_events = on_fetch_events

        if on_click:
            self.on("click", lambda e: handle_event(on_click, e), args=["info"])
        if on_fetch_events:
            self.on("fetch_events", self._handle_fetch_events)

    def add_event(self, title: str, start: str, end: str, **kwargs) -> None:
        """Add an event to the calendar.

        :param title: title of the event
        :param start: start time of the event
        :param end: end time of the event
        """
        event_dict = {"title": title, "start": start, "end": end, **kwargs}
        self._props["options"]["events"].append(event_dict)
        self.update()
        self.run_method("update_calendar")

    def remove_event(self, title: str, start: str, end: str) -> None:
        """Remove an event from the calendar.

        :param title: title of the event
        :param start: start time of the event
        :param end: end time of the event
        """
        for event in self._props["options"]["events"]:
            if event["title"] == title and event["start"] == start and event["end"] == end:
                self._props["options"]["events"].remove(event)
                break

        self.update()
        self.run_method("update_calendar")

    def _handle_fetch_events(self, e: GenericEventArguments) -> None:
        """Bridge JS -> Python : FullCalendar needs events."""
        # e.args = {'startStr': ..., 'endStr': ..., 'timeZone': ...}
        handler = self._on_fetch_events
        assert handler is not None
        arguments = GenericEventArguments(sender=self, client=self.client, args=e.args)

        if inspect.signature(handler).parameters:
            result = handler(arguments)
        else:
            result = handler()

        if isinstance(result, Awaitable):
            # Asynchronous callback -> scheduled as a background task
            background_tasks.create(self._process_fetch_result(result))
        else:
            # Synchronous callback -> send immediately
            self._send_events(result)

    async def _process_fetch_result(self, result: Awaitable) -> None:
        events = await result
        self._send_events(events)

    def _send_events(self, events: list[dict]) -> None:
        """Bridge Python -> JS : send events to FullCalendar."""
        self.run_method("provide_events", events)

    @property
    def events(self) -> list[dict[str, Any]]:
        """List of events to display on the calendar."""
        return self._props["options"].get("events", [])
