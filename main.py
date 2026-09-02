#!/usr/bin/env python3
"""
FullCalendar + NiceGUI demo application.

Features
--------
- Displays a calendar with hardcoded sample events and user-created events.
- Loads 1 year of generated sample events from ``events_full.json`` only when
  the user changes the calendar view/range via ``fetch_events_from_python``.
  This keeps the UI fast: only the events for the visible date range are sent.
- Persists events created from the form into ``events.json`` so they survive
  page reloads.
- Provides a standalone "Add Event" dialog defined in ``event_form.py``.

Run
---
    python main.py
"""
import json
import os
from datetime import datetime

import requests
from event_form import create_add_event_dialog
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fullcalendar_comp import FullCalendar as fullcalendar

from nicegui import app, events, ui

ui.add_head_html("""
<style>
.selected-day {
    box-shadow: inset 0 0 0 999px rgba(79, 70, 229, 0.15) !important;
}
</style>
""")

# ---------------------------------------------------------------------------
# CORS middleware
# NiceGUI's script mode re-executes this file via runpy; guard against the
# second run when the app is already started (otherwise add_middleware raises
# "Cannot add middleware after an application has started").
# ---------------------------------------------------------------------------
if not app.is_started:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

mintime = "00:00:00"
maxtime = "23:59:00"
EVENTS_FILE = "./events_dat/events.json"


def load_saved_events():
    """Read previously saved events from ``events.json``.

    Returns:
        list: A list of event dicts. Returns an empty list if the file does not exist yet.
    """
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


# ---------------------------------------------------------------------------
# Static event sources
# ---------------------------------------------------------------------------
def get_events():
    """Return a mix of hardcoded sample events and user-created events.

    FullCalendar will load these once when the calendar initialises.

    Returns:
        list: Combined list of hardcoded demo events and saved user events.
    """
    hardcoded_events = [
        {
            "title": "Math",
            "start": datetime.now().strftime(r"%Y-%m-%d") + " 08:00:00",
            "end": datetime.now().strftime(r"%Y-%m-%d") + " 10:00:00",
            "color": "red",
        },
        {
            "title": "Physics",
            "start": datetime.now().strftime(r"%Y-%m-%d") + " 10:00:00",
            "end": datetime.now().strftime(r"%Y-%m-%d") + " 12:00:00",
            "color": "green",
        },
        {
            "title": "Chemistry",
            "start": datetime.now().strftime(r"%Y-%m-%d") + " 13:00:00",
            "end": datetime.now().strftime(r"%Y-%m-%d") + " 15:00:00",
            "color": "blue",
        },
        {
            "title": "Biology",
            "start": datetime.now().strftime(r"%Y-%m-%d") + " 15:00:00",
            "end": datetime.now().strftime(r"%Y-%m-%d") + " 17:00:00",
            "color": "orange",
        },
    ]
    return load_saved_events() + hardcoded_events


# ---------------------------------------------------------------------------
# Dynamic event source
# ---------------------------------------------------------------------------
# Get event on View selection (Example you select a Month view)
def fetch_events_from_python(info):
    """Called by FullCalendar when the visible date range changes.

    Instead of loading ALL events at once (which would be slow for a year of
    data), this function opens ``events_full.json`` and returns only the events
    whose start time falls inside the requested window.

    Args:
        info: Event info object from FullCalendar. Its ``args`` dict contains:
            - ``startStr``: ISO start of the visible window.
            - ``endStr``: ISO end of the visible window.

    Returns:
        list: Events from ``events_full.json`` that fall within the requested range.
    """
    start = datetime.fromisoformat(info.args["startStr"][:19])
    end = datetime.fromisoformat(info.args["endStr"][:19])

    with open("./events_data/events_full.json", encoding="utf-8") as f:
        all_events = json.load(f)

    filtered = []
    for ev in all_events:
        ev_start = datetime.fromisoformat(ev["start"][:19])
        if start <= ev_start < end:
            filtered.append(ev)

    ui.notify(f"Chargement : {len(filtered)} événements sur la période demandée")
    return filtered


# ---------------------------------------------------------------------------
# Backend routes
# ---------------------------------------------------------------------------
# Add proxy endpoint to fetch ICS data
@app.get("/proxy-ics")
def proxy_ics(ics_url: str | None = None):
    """Proxy endpoint to fetch external ICS calendar files.

    Args:
        ics_url: URL of the ICS file to fetch.

    Returns:
        Response: The ICS file content with the correct media type, or an error response.
    """
    if not ics_url:
        return Response(content="Erreur: aucune URL ICS fournie.", status_code=400)
    response = requests.get(ics_url)
    if response.status_code == 200:
        return Response(content=response.text, media_type="text/calendar")
    return Response(status_code=404)


# ---------------------------------------------------------------------------
# Event creation
# ---------------------------------------------------------------------------
def add_event_to_db(data):
    """Save a new event to ``events.json`` and refresh the calendar.

    Args:
        data (dict): Dictionary produced by the ``event_form`` dialog containing keys
            such as ``event_title``, ``event_start_date``, ``event_start_time``,
            ``all_day``, ``rrule`` (for recurring events), etc.
    """
    start_time = data.get("event_start_time", "00:00")
    start = datetime.combine(
        datetime.strptime(data["event_start_date"], "%Y-%m-%d"),
        datetime.strptime(start_time, "%H:%M").time(),
    ).isoformat()

    event = {
        "title": data.get("event_title", "Untitled"),
        "start": start,
        "allDay": data.get("all_day", False),
    }

    if data.get("rrule"):
        event["rrule"] = data["rrule"]
    else:
        end_time = data.get("event_end_time", "23:59")
        end = datetime.combine(
            datetime.strptime(data.get("event_end_date", data["event_start_date"]), "%Y-%m-%d"),
            datetime.strptime(end_time, "%H:%M").time(),
        ).isoformat()
        event["end"] = end

    events = load_saved_events()
    events.append(event)

    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    ui.notify(
        message=f"Événement ajouté : {data['event_title']} à {start}",
        title=data["event_title"],
        color="green",
    )
    create_calendar.refresh()


def handle_click(event: events.GenericEventArguments):
    """React to clicks on the calendar (dates or existing events)."""
    if "info" in event.args:
        if "event" in event.args["info"]:
            ui.notify(f"eventclick: {event.args['info']['event']}")  # For event click
        else:
            ui.notify(f"dateclick: {event.args['info']['date']}")  # For Date click


# ---------------------------------------------------------------------------
# Calendar rendering
# ---------------------------------------------------------------------------
@ui.refreshable
def create_calendar():
    """Build and render the FullCalendar instance.

    ``@ui.refreshable`` means calling ``create_calendar.refresh()`` will
    redraw the calendar without reloading the whole page.
    """
    options = {
        "locale": "fr",  # example with other locales can be found here https://fullcalendar.io/docs/locale-demo
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "today",
            "center": "title",
            "right": "multiMonthYear,dayGridMonth,timeGridWeek,timeGridDay,listWeek",
        },
        "footerToolbar": {"right": "prev,next"},
        "slotMinTime": mintime,
        "slotMaxTime": maxtime,
        "duration": "01:00:00",
        "allDaySlot": True,
        "timeZone": "Europe/Paris",  # Example with other Timezone available here https://fullcalendar.io/docs/timeZone-demo
        "height": "auto",
        "selectable": True,  # need to be activated in order to make dateClick available
        "weekNumbers": True,  # to show weeknumbers in calendars
        "eventSources": [
            get_events(),  # static + saved user events
            {
                "url": "/proxy-ics?ics_url=https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-A.ics",
                "format": "ics",
                "color": "blue",
            },  # Example of ICS file
            [   #Here an example of recurring event"
                {
                    "title": "my recurring event",
                    "rrule": {
                        "freq": "weekly",
                        "interval": 5,
                        "byweekday": ["mo", "fr"],
                        "dtstart": "2025-02-01T10:30:00",  # will also accept '20120201T103000'
                        "until": "2025-06-01",  # will also accept '20120201'
                    },
                }
            ],
        ],
    }
    fullcalendar(
        options, on_click=handle_click, on_fetch_events=fetch_events_from_python
    )  # New Options to fetch events on view selection


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------
with ui.row():
    ui.page_title("Events")
    create_calendar()

    add_event = create_add_event_dialog(submit_callback=add_event_to_db)
    ui.button("Add Event", on_click=add_event.open).classes("text-xs")


ui.run(port=8085)
