
# This script is a simple example of how to use the FullCalendar component with an ics file.
from typing import Optional

import requests
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fullcalendar import FullCalendar

from nicegui import app, ui

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add proxy endpoint to fetch ICS data
@app.get("/proxy-ics")
def proxy_ics(ics_url: Optional[str] = None):
    if not ics_url:
        return Response(
            content="Erreur: aucune URL ICS fournie.",
            status_code=400
        )
    response = requests.get(ics_url)
    if response.status_code == 200:
        return Response(
            content=response.text,
            media_type="text/calendar"
        )
    return Response(status_code=404)

options = {
    'themeSystem': 'bootstrap5',
    'initialView': 'multiMonthYear',
    'headerToolbar': {
        'left': 'today',
        'center': 'title',
        'right': 'dayGridMonth,timeGridWeek,timeGridDay, listWeek'
    },
    'footerToolbar': {'right': 'prev,next'},
    'duration': '01:00:00',
    'allDaySlot': True,
    'timeZone': 'local',
    'height': 'auto',
    'selectable': True,
    'weekNumbers': True,
    'events': [
    {
        'title': 'my recurring event',
        'rrule': {
            'freq': 'weekly',
            'interval': 5,
            'byweekday': [ 'mo', 'fr' ],
            'dtstart': '2025-02-01T10:30:00', #will also accept '20120201T103000'
            'until': '2025-06-01' #will also accept '20120201'
            }
        }
    ],
}

calendar = FullCalendar(options)
print(calendar.events)
ui.run(port=8084)
