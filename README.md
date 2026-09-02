# NiceGui FullCalendar Example

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/dorel14/NiceGui-FullCalendar_more_Options/blob/master/README.md)
[![fr](https://img.shields.io/badge/lang-fr-green.svg)](https://github.com/dorel14/NiceGui-FullCalendar_more_Options/blob/master/README.fr.md)

**This example is designed for NiceGui with non-premium FullCalendar plugins enabled.**

## Plugins Used

- **@fullcalendar/daygrid**: Provides Month and DayGrid views: `dayGridYear`, `dayGridMonth`, `dayGridWeek`, `dayGridDay`, `dayGrid` (generic)
- **@fullcalendar/timegrid**: Provides TimeGrid views: `timeGridWeek`, `timeGridDay`, `timeGrid` (generic)
- **@fullcalendar/list**: Provides List views: `listYear`, `listMonth`, `listWeek`, `listDay`, `list` (generic)
- **@fullcalendar/multimonth**: Provides Multi-Month views: `multiMonthYear`, `multiMonth` (generic)
- **@fullcalendar/icalendar**: For loading events from an iCalendar feed
- **@fullcalendat/rrule**: For handling recurring events via rrule

## Features

- **Event Creation Form**: A form to create events.
- **Date and Event Click Handling**: Some code to handle date clicks and event clicks.

## Instructions

1. Clone this repository.

## Code Example

An example code for event creation is present in the `main.py` file.

## Dynamic Event Fetching

Instead of loading all events at init time, you can let the calendar request events on-demand (e.g. per month/week) via a Python callback. This is useful for large datasets.

See the working example in [`basic_main.py`](basic_main.py).

> The fetch mechanism is implemented in [`fullcalendar.py`](fullcalendar.py) and [`fullcalendar.js`](fullcalendar.js) — make sure these files are in the same folder as your script.

### Quick-start

1. In your `options` dict, set `events` to any callable (e.g. `lambda *a, **k: None`).
2. Pass an `on_fetch_events` callback to `FullCalendar`.
3. Inside the callback, build the list of events and call `info.response(events_list)`.

```python
from fullcalendar import FullCalendar as fullcalendar

options = {
    "initialView": "dayGridMonth",
    "events": lambda *a, **k: None,  # enables fetch mode
}

def on_fetch(info):
    # info.start / info.end  -> ISO date strings
    # info.start_value / info.end_value -> epoch ms (for DB range queries)
    events = load_events_from_database(info.start, info.end)
    info.response(events)   # send the list back to the calendar

fullcalendar(options, on_fetch_events=on_fetch)
```

### What the callback receives

`FetchInfoArguments` exposes:

| attribute       | type | description                                         |
|-----------------|------|-----------------------------------------------------|
| `start`         | `str` | ISO string of the visible range start (inclusive).  |
| `end`           | `str` | ISO string of the visible range end (exclusive).   |
| `start_value`   | `int` | start as epoch milliseconds (useful for DB queries).|
| `end_value`     | `int` | end as epoch milliseconds.                          |
| `time_zone`     | `str` | the calendar's timeZone setting.                    |
| `request_id`    | `int` | internal id used to correlate the response.         |

> FullCalendar calls `on_fetch_events` automatically whenever the user navigates views. Only events intersecting the requested range are returned.

The `FetchInfoArguments` class and the calendar integration live in [`fullcalendar.py`](fullcalendar.py) / [`fullcalendar.js`](fullcalendar.js).

### Error handling

Call `info.failure("message")` instead of `info.response(...)` to signal an error to FullCalendar (e.g. a database timeout).

## Screenshots

![Add Event](./screenshots/add-event.png)
![Week View](./screenshots/weekview.png)
![Multi-Month View + iCal Calendar](./screenshots/multimonth+ical.png)

## Contributions

Contributions are welcome! Please submit a pull request or open an issue to discuss the changes you want to make.
