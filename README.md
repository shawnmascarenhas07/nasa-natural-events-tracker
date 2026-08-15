# NASA Natural Events Tracker

A Flask web application that shows natural events such as wildfires, storms, floods and
volcanoes using live data from NASA's Earth Observatory Natural Event Tracker (EONET) API.
Events can be browsed and filtered by category, status and how far back to search, and every
event has its own detail page showing its location, date and magnitude where NASA provides
one. Events can also be saved to a personal watch list stored in a local SQLite database,
where each saved event can be given a short note.

## Setup

1. Create a virtual environment:

   ```
   python -m venv .venv
   ```

2. Activate it.

   On Windows:

   ```
   .venv\Scripts\activate
   ```

   On macOS or Linux:

   ```
   source .venv/bin/activate
   ```

3. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Start the application:

   ```
   flask run
   ```

5. Open http://127.0.0.1:5000/ in a browser.

The database file `events.db` is created automatically the first time the application starts,
so there is no manual database setup. An internet connection is needed because the event data
comes from NASA's API.

To check the classes and the API connection from the terminal:

```
python test_models.py
```

## OOP design

The three classes live in `models.py` and are imported by `app.py`.

**NaturalEvent** represents one event from the EONET API. It stores the title, category,
status, latitude, longitude, date, magnitude, magnitude unit and source URL. The EONET id is
kept in a private attribute `__eonet_id` and read through the getter `get_eonet_id()`, which
is where the project demonstrates encapsulation. The method `is_active()` returns True when
the status is "open", and `summary()` returns a short description containing the category,
title and status.

**WatchedEvent** inherits from NaturalEvent and represents an event that has been saved to
the watch list. It calls `super().__init__()` for the shared attributes and adds `note` and
`alert_active`. The method `toggle_alert()` flips `alert_active` and returns the new value,
and `summary()` overrides the parent version by calling `super().summary()` and adding the
note and alert state.

**EventFetcher** handles every request to the EONET API. `fetch_events()` calls the
`/api/v3/events` endpoint and returns a list of NaturalEvent objects, and `fetch_event()`
calls `/api/v3/events/<id>` and returns a single one. Both use `build_event()`, which turns
one raw dictionary from the API into a NaturalEvent object. The Flask routes never call
`requests` themselves, they always go through this class.

## Main features

- Browse live events from NASA's EONET API, refreshed on every request.
- Filter the browse page by category, status and number of days, with the chosen values kept
  in the form after submitting.
- A detail page for each event showing title, category, status, date, latitude, longitude,
  source link, and magnitude with its unit when NASA provides one.
- A personal watch list stored in SQLite, with events added from either the browse page or the
  detail page.
- Adding the same event twice does not create a duplicate row.
- Removing an event asks for confirmation first.
- A personal note can be added to or edited on any saved event, and empty notes are allowed.
- Events already on the watch list are marked as saved on the browse and detail pages.
- Flash messages confirm adding, removing and saving a note.
- All pages share one layout through `base.html` using template inheritance.
- If the API cannot be reached, the pages show a message instead of crashing.

## Known limitations and omitted features

- Group D (search, filter and sort on the watch list) and Group E (statistics) were made
  optional by the instructor and are not implemented.
- There is no statistics page, so `templates/stats.html` from the suggested folder structure
  is not included.
- The `search_log` table is created because criterion A2 requires all three tables to exist,
  but nothing writes to it, since search logging belongs to feature D1 which is out of scope.
- The stretch features (alert toggle, CSV export, pagination, category bar chart) are not
  implemented. The only stretch item included is the simple API error handling, because a
  network failure would otherwise break the browse and detail pages.
- `WatchedEvent.toggle_alert()` exists and is tested because criterion A3 requires it, but
  there is no button for it in the interface, as alert toggling is a stretch feature.
- The watch list is not tied to a user account, so there is one shared watch list.
- Events that cover an area rather than a single point, such as some floods, are stored
  without coordinates and show "Not provided" instead.
- The browse page requests up to 50 events at a time.

## Development assistance

I used an AI assistant (Claude) while building this project, mainly to help plan the structure,
review my code and test it against the assignment criteria. I have gone through the code and
understand how each part works.
