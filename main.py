#!/usr/bin/env python3
from datetime import date, datetime, timedelta
from typing import Any

import requests
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

mintime = '00:00:00'
maxtime = '23:59:00'
today = date.today().strftime("%Y-%m-%d")
nowhour = datetime.now().strftime("%H:%M")


#To get events from DB or other format
def get_events():
    events = [
        {
            'title': 'Math',
            'start': datetime.now().strftime(r'%Y-%m-%d') + ' 08:00:00',
            'end': datetime.now().strftime(r'%Y-%m-%d') + ' 10:00:00',
            'color': 'red',
        },
        {
            'title': 'Physics',
            'start': datetime.now().strftime(r'%Y-%m-%d') + ' 10:00:00',
            'end': datetime.now().strftime(r'%Y-%m-%d') + ' 12:00:00',
            'color': 'green',
        },
        {
            'title': 'Chemistry',
            'start': datetime.now().strftime(r'%Y-%m-%d') + ' 13:00:00',
            'end': datetime.now().strftime(r'%Y-%m-%d') + ' 15:00:00',
            'color': 'blue',
        },
        {
            'title': 'Biology',
            'start': datetime.now().strftime(r'%Y-%m-%d') + ' 15:00:00',
            'end': datetime.now().strftime(r'%Y-%m-%d') + ' 17:00:00',
            'color': 'orange',
        },
    ]
    return events

#Get event on View selection (Example you select a Month view)
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
    start = datetime.fromisoformat(info.args['startStr'][:19])
    end = datetime.fromisoformat(info.args['endStr'][:19])

    day = start
    while day < end:
        day_str = day.strftime('%Y-%m-%d')
        for hour in range(8, 18, 2):
            events.append({
                'title': f'Séance automatique ({day_str})',
                'start': f'{day_str} {hour:02d}:00:00',
                'end':   f'{day_str} {hour + 1:02d}:00:00',
                'color': 'purple',
            })
        day += timedelta(days=1)
    return events


# Add proxy endpoint to fetch ICS data
@app.get("/proxy-ics")
def proxy_ics(ics_url: str | None = None):
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

def add_event_to_db(data):
    if 'rrule' in data:
        ui.notify(f'title={data["event_title"]}, \
        rrule={data["rrule"]}, \
        color="white"')
        start = datetime.combine(
            datetime.strptime(data['event_start_date'], "%Y-%m-%d"),
            datetime.strptime(data['event_start_time'], "%H:%M").time()
        ).isoformat()
        ui.notify(
            message=f"Événement récurrent ajouté : {data['event_title']} à {start}",
            title=data['event_title'],
        )
    else:
        ui.notify(f'title={data["event_title"]}, \
        start={datetime.combine(datetime.strptime(data["event_start_date"], "%Y-%m-%d"),\
                datetime.strptime(data["event_start_time"], "%H:%M").time())}, \
        color="white"')
        start = datetime.combine(
            datetime.strptime(data['event_start_date'], "%Y-%m-%d"),
            datetime.strptime(data['event_start_time'], "%H:%M").time()
        ).isoformat()
        ui.notify(
            message=f"Événement ajouté : {data['event_title']} à {start}",
            title=data['event_title'],
        )


def handle_click(event: events.GenericEventArguments):
    if 'info' in event.args:
        if 'event' in event.args['info']:
            ui.notify(f'eventclick: {event.args['info']['event']}') #For event click
        else:
            ui.notify(f'dateclick: {event.args['info']['date']}') #For Date click


@ui.refreshable
def create_calendar():
    options = {
        'locale': 'fr', #example with other locales can be found here https://fullcalendar.io/docs/locale-demo
        'initialView': 'dayGridMonth',
        'headerToolbar': {'left': 'today',
                            'center':'title',
                            'right': 'multiMonthYear, dayGridMonth, timeGridWeek, daySelected, listWeek'
                        },
        'footerToolbar': {'right': 'prev,next'},
        'slotMinTime': mintime,
        'slotMaxTime': maxtime,
        'duration': '01:00:00',
        'allDaySlot': False,
        'timeZone': 'Europe/Paris', #Example with other Timezone available here https://fullcalendar.io/docs/timeZone-demo
        'height': 'auto',
        'selectable': True, #need to be activated in order to make dateClick available
        'weekNumbers': True, #to show weeknumbers in calendars
        'eventSources':[
            get_events(), #can be replaced with a list of events
            {
            'url': '/proxy-ics?ics_url=https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-A.ics',
            'format': 'ics',
            'color': 'blue'
        }, #Example of ICS file
        [{
        'title': 'my recurring event',
        'rrule': {
            'freq': 'weekly',
            'interval': 5,
            'byweekday': [ 'mo', 'fr' ],
            'dtstart': '2025-02-01T10:30:00', #will also accept '20120201T103000'
            'until': '2025-06-01' #will also accept '20120201'
            }
        }],
        ]
        }
    fullcalendar(options, on_click=handle_click,
                on_fetch_events=fetch_events_from_python) #New Options to fetch events on view selection


with ui.row():
    ui.page_title("Events")
    create_calendar()
    with ui.dialog() as add_event, ui.card():
        data: dict[str, Any] = {'rrule': {}}  # Initialize data with rrule dict

        from typing import Any

        def update_rrule(key: str, value: Any):
            data['rrule'][key] = value

        ui.label('Add Event')
        ui.input('Event Title', placeholder='Event Title').on_value_change(lambda e: data.update({'event_title': e.value}))
        all_day = ui.checkbox('All Day', value=False).on_value_change(lambda e: data.update({'all_day': e.value}))
        recurring = ui.checkbox('Recurring Event', value=False)


        with ui.grid(columns=2):
            with ui.column():
                ui.label('Start date')
                with ui.input('Start Date').on_value_change(lambda e: data.update({'event_start_date': e.value})) as date:
                    with ui.menu().props('no-parent-event') as datemenu:
                        with ui.date(value=today).bind_value(date):
                            with ui.row().classes('justify-end'):
                                ui.button('Close', on_click=datemenu.close).props('flat')
                    with date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', datemenu.open).classes('cursor-pointer')

            with ui.column().bind_visibility_from(all_day, 'value', value=False):
                ui.label('Start time')
                with ui.input('Start Time').on_value_change(lambda e: data.update({'event_start_time': e.value})) as time:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.time(value=nowhour).bind_value(time):
                            with ui.row().classes('justify-end'):
                                ui.button('Close', on_click=menu.close).props('flat')
                    with time.add_slot('append'):
                        ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')

            with ui.column():
                ui.label('End date')
                with ui.input('End Date').on_value_change(lambda e: data.update({'event_end_date': e.value})) as date:
                    with ui.menu().props('no-parent-event') as datemenu:
                        with ui.date(value=today).bind_value(date):
                            with ui.row().classes('justify-end'):
                                ui.button('Close', on_click=datemenu.close).props('flat')
                    with date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', datemenu.open).classes('cursor-pointer')

            with ui.column().bind_visibility_from(all_day, 'value', value=False):
                ui.label('End time')
                with ui.input('End Time').on_value_change(lambda e: data.update({'event_end_time': e.value})) as time:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.time(value=nowhour).bind_value(time):
                            with ui.row().classes('justify-end'):
                                ui.button('Close', on_click=menu.close).props('flat')
                    with time.add_slot('append'):
                        ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')

            with ui.column().bind_visibility_from(recurring, 'value'):
                ui.label('Recurrence Settings')
                with ui.grid(columns=2):
                    ui.select(
                        ['daily', 'weekly', 'monthly', 'yearly'],
                        value='weekly',
                        label='Frequency'
                ).on_value_change(lambda e: update_rrule('freq', e.value))
                ui.number(
                    'Interval',
                    min=1
                ).on_value_change(lambda e: update_rrule('interval', e.value))
                with ui.column().bind_visibility_from(data['rrule'], 'freq', value='weekly'):
                    ui.label('Repeat on')
                    weekdays = []
                    with ui.row():
                        for day in ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']:
                            ui.checkbox(day.capitalize()).on_value_change(
                        lambda e, d=day: (
                                    weekdays.append(d) if e.value and d not in weekdays
                                    else weekdays.remove(d) if d in weekdays else None,
                    update_rrule('byweekday', weekdays)
                    )[1]
            )
        ui.textarea('Event Description', placeholder='Event description').on_value_change(lambda e: data.update({'event_description': e.value})).classes('w-full')

        def on_submit():
            if recurring.value:
                # Add dtstart to rrule using start date/time
                data['rrule']['dtstart'] = f"{data['event_start_date']}T{data['event_start_time']}"
                # Add until using the end recurrence date
                data['rrule']['until'] = data['until']
            add_event_to_db(data)
        with ui.row():
            ui.button('Add Event', on_click=on_submit, icon='add').classes('text-xs')
            ui.button('Cancel', icon='close', on_click=add_event.close).classes('text-xs')


    ui.button('Add Event', on_click=add_event.open).classes('text-xs')


ui.run(port=8085)
