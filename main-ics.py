
# This script is a simple example of how to use the FullCalendar component with an ics file.
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
def proxy_ics():
    ics_url = 'https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-A-B-C-Corse.ics'
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
    'events': {
        'url': '/proxy-ics',  # Use local proxy endpoint to fetch ICS data
        'format': 'ics'
    },
}

calendar = FullCalendar(options)
print(calendar.events)
ui.run(port=8084)
