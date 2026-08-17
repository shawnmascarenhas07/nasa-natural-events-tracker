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

The main classes are in models.py.

- NaturalEvent represents one event from NASA.
- WatchedEvent inherits from NaturalEvent and adds watch-list data.
- EventFetcher handles requests to the NASA API.

## Main features

- Browse live NASA EONET events.
- Filter events by category, status, and days.
- Open a detail page for each event.
- Save events to a watch list.
- Add notes to saved events.
- Remove events from the watch list.
- Show flash messages after actions.
- Show an error message if the NASA API cannot be reached.

## Limitations

- The watch list is local and has no user accounts.
- Some NASA events do not provide magnitude or coordinates.
- Group D and Group E were optional and are not implemented.
- The app needs internet to load live NASA data.

## Development assistance

AI assistance was used during development for planning, implementation support, review, and testing.
