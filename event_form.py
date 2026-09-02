"""
Reusable "Add Event" dialog for NiceGUI + FullCalendar.

This module provides a single public function, ``create_add_event_dialog``,
that builds a modal form allowing users to create one-time or recurring events.
The form is completely independent: you only need to pass it a callback that
receives the collected data as a dictionary.

Files
-----
event_form.py
    The reusable dialog component (this file).
main.py
    Example app that uses the dialog and persists events to JSON.
generate_events.py
    Standalone script to generate ``events_full.json`` with 1 year of sample data.

Usage
-----
    from event_form import create_add_event_dialog

    def my_callback(data: dict) -> None:
        # ``data`` contains keys like:
        #   event_title, event_start_date, event_start_time,
        #   all_day, rrule (for recurring events), etc.
        print("New event:", data)

    dialog = create_add_event_dialog(submit_callback=my_callback)
    ui.button("Add Event", on_click=dialog.open)
"""
from collections.abc import Callable
from datetime import date, datetime
from typing import Any, Optional

from nicegui import ui


def create_add_event_dialog(
    submit_callback: Callable[[dict], None] = lambda data: None,
    today: Optional[str] = None,
    nowhour: Optional[str] = None,
):
    """Create a reusable "Add Event" dialog.

    The dialog contains:
    - Event title input
    - All-day checkbox
    - Start / end date and time pickers
    - Recurrence settings (frequency, interval, weekdays, end date)
    - Event description textarea

    Args:
        submit_callback (Callable[[dict], None]): A function called when the user
            clicks "Add Event". It receives the ``data`` dictionary with all form
            values so you can save the event however you like (database, JSON file,
            API call, etc.).
        today (str, optional): Default date shown in the date pickers, formatted
            as ``YYYY-MM-DD``. Defaults to today's date if omitted.
        nowhour (str, optional): Default time shown in the time pickers, formatted
            as ``HH:mm``. Defaults to the current time if omitted.

    Returns:
        ui.dialog: The dialog element. Call ``.open()`` to show it and ``.close()``
        to hide it.
    """
    if today is None:
        today = date.today().strftime("%Y-%m-%d")
    if nowhour is None:
        nowhour = datetime.now().strftime("%H:%M")

    with ui.dialog() as add_event:
        with ui.card():
            # ``data`` collects every field value so we can pass it to the
            # ``submit_callback`` on submit.
            data: dict[str, Any] = {"rrule": {}}

            def update_rrule(key: str, value: Any):
                data["rrule"][key] = value

            ui.label("Add Event")
            ui.input("Event Title", placeholder="Event Title").on_value_change(
                lambda e: data.update({"event_title": e.value})
            )
            all_day = ui.checkbox("All Day", value=False).on_value_change(lambda e: data.update({"all_day": e.value}))
            recurring = ui.checkbox("Recurring Event", value=False)

            with ui.grid(columns=2):
                with ui.column():
                    ui.label("Start date")
                    with ui.input("Start Date").on_value_change(
                        lambda e: data.update({"event_start_date": e.value})
                    ) as date_input:
                        with ui.menu().props("no-parent-event") as datemenu:
                            with ui.date(value=today).bind_value(date_input):
                                with ui.row().classes("justify-end"):
                                    ui.button("Close", on_click=datemenu.close).props("flat")
                        with date_input.add_slot("append"):
                            ui.icon("edit_calendar").on("click", datemenu.open).classes("cursor-pointer")

                with ui.column().bind_visibility_from(all_day, "value", value=False):
                    ui.label("Start time")
                    with ui.input("Start Time").on_value_change(
                        lambda e: data.update({"event_start_time": e.value})
                    ) as time_input:
                        with ui.menu().props("no-parent-event") as menu:
                            with ui.time(value=nowhour).bind_value(time_input):
                                with ui.row().classes("justify-end"):
                                    ui.button("Close", on_click=menu.close).props("flat")
                        with time_input.add_slot("append"):
                            ui.icon("access_time").on("click", menu.open).classes("cursor-pointer")

                with ui.column():
                    ui.label("End date")
                    with ui.input("End Date").on_value_change(
                        lambda e: data.update({"event_end_date": e.value})
                    ) as date_input:
                        with ui.menu().props("no-parent-event") as datemenu:
                            with ui.date(value=today).bind_value(date_input):
                                with ui.row().classes("justify-end"):
                                    ui.button("Close", on_click=datemenu.close).props("flat")
                        with date_input.add_slot("append"):
                            ui.icon("edit_calendar").on("click", datemenu.open).classes("cursor-pointer")

                with ui.column().bind_visibility_from(all_day, "value", value=False):
                    ui.label("End time")
                    with ui.input("End Time").on_value_change(
                        lambda e: data.update({"event_end_time": e.value})
                    ) as time_input:
                        with ui.menu().props("no-parent-event") as menu:
                            with ui.time(value=nowhour).bind_value(time_input):
                                with ui.row().classes("justify-end"):
                                    ui.button("Close", on_click=menu.close).props("flat")
                        with time_input.add_slot("append"):
                            ui.icon("access_time").on("click", menu.open).classes("cursor-pointer")

                with ui.column().bind_visibility_from(recurring, "value"):
                    ui.label("Recurrence Settings")
                    with ui.grid(columns=2):
                        ui.select(
                            ["daily", "weekly", "monthly", "yearly"], value="weekly", label="Frequency"
                        ).on_value_change(lambda e: update_rrule("freq", e.value))
                        ui.number("Interval", min=1).on_value_change(lambda e: update_rrule("interval", e.value))

                        with ui.column().bind_visibility_from(data["rrule"], "freq", value="weekly"):
                            ui.label("Repeat on")
                            weekdays = []
                            with ui.row():
                                for day in ["mo", "tu", "we", "th", "fr", "sa", "su"]:
                                    ui.checkbox(day.capitalize()).on_value_change(
                                        lambda e, d=day: (
                                            weekdays.append(d) if e.value and d not in weekdays
                                            else weekdays.remove(d) if d in weekdays else None,
                                            update_rrule("byweekday", weekdays),
                                        )[1]
                                    )

                        ui.input("End recurrence date", placeholder="YYYY-MM-DD").on_value_change(
                            lambda e: data.update({"until": e.value})
                        )

            ui.textarea("Event Description", placeholder="Event description").on_value_change(
                lambda e: data.update({"event_description": e.value})
            ).classes("w-full")

            def on_submit():
                # If the event is recurring, assemble the dtstart/until fields
                # expected by FullCalendar.
                if recurring.value:
                    data["rrule"]["dtstart"] = f"{data['event_start_date']}T{data['event_start_time']}"
                    data["rrule"]["until"] = data.get("until")
                submit_callback(data)
                add_event.close()

            with ui.row():
                ui.button("Add Event", on_click=on_submit, icon="add").classes("text-xs")
                ui.button("Cancel", icon="close", on_click=add_event.close).classes("text-xs")

    return add_event
