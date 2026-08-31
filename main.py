#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

import requests
from event_form import create_add_event_dialog
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fullcalendar import FullCalendar as fullcalendar

from nicegui import app, events, ui

# Add CORS middleware configuration.
# NiceGUI's script mode re-executes this file via runpy; guard against the
# second run when the app is already started (otherwise add_middleware raises
# "Cannot add middleware after an application has started").
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
EVENTS_FILE = "events.json"


def load_saved_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


# To get events from DB or other format
def get_events():
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


# Get event on View selection (Example you select a Month view)
def fetch_events_from_python(info):
    """
    Équivalent JS de :
        events: function(fetchInfo, successCallback) {
            // build events...
            successCallback(events);
        }
    """
    # info.args contient startStr, endStr, timeZone
    ui.notify(f"Chargement événements : {info.args['startStr']} → {info.args['endStr']}")

    events = []
    # Ne charger QUE les événements de la période demandée [start, end).
    # FullCalendar fournit startStr/endStr dans la timeZone du calendrier.
    start = datetime.fromisoformat(info.args["startStr"][:19])
    end = datetime.fromisoformat(info.args["endStr"][:19])

    day = start
    while day < end:
        day_str = day.strftime("%Y-%m-%d")
        for hour in range(8, 18, 2):
            events.append(
                {
                    "title": f"Séance automatique ({day_str})",
                    "start": f"{day_str} {hour:02d}:00:00",
                    "end": f"{day_str} {hour + 1:02d}:00:00",
                    "color": "purple",
                }
            )
        day += timedelta(days=1)
    return events


# Add proxy endpoint to fetch ICS data
@app.get("/proxy-ics")
def proxy_ics(ics_url: str | None = None):
    if not ics_url:
        return Response(content="Erreur: aucune URL ICS fournie.", status_code=400)
    response = requests.get(ics_url)
    if response.status_code == 200:
        return Response(content=response.text, media_type="text/calendar")
    return Response(status_code=404)


def add_event_to_db(data):
    start_time = data.get("event_start_time", "00:00")
    start = datetime.combine(
        datetime.strptime(data["event_start_date"], "%Y-%m-%d"), datetime.strptime(start_time, "%H:%M").time()
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
    if "info" in event.args:
        if "event" in event.args["info"]:
            ui.notify(f"eventclick: {event.args['info']['event']}")  # For event click
        else:
            ui.notify(f"dateclick: {event.args['info']['date']}")  # For Date click


@ui.refreshable
def create_calendar():
    options = {
        "locale": "fr",  # example with other locales can be found here https://fullcalendar.io/docs/locale-demo
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "today",
            "center": "title",
            "right": "multiMonthYear, dayGridMonth, timeGridWeek, daySelected, listWeek",
        },
        "footerToolbar": {"right": "prev,next"},
        "slotMinTime": mintime,
        "slotMaxTime": maxtime,
        "duration": "01:00:00",
        "allDaySlot": False,
        "timeZone": "Europe/Paris",  # Example with other Timezone available here https://fullcalendar.io/docs/timeZone-demo
        "height": "auto",
        "selectable": True,  # need to be activated in order to make dateClick available
        "weekNumbers": True,  # to show weeknumbers in calendars
        "eventSources": [
            get_events(),  # can be replaced with a list of events
            {
                "url": "/proxy-ics?ics_url=https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-A.ics",
                "format": "ics",
                "color": "blue",
            },  # Example of ICS file
            [
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


with ui.row():
    ui.page_title("Events")
    create_calendar()
    add_event = create_add_event_dialog(submit_callback=add_event_to_db)
    ui.button("Add Event", on_click=add_event.open).classes("text-xs")


ui.run(port=8085)
