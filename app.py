"""NASA Natural Events Tracker."""

import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for
from requests.exceptions import RequestException

from models import EventFetcher, WatchedEvent

DB_PATH = "events.db"

# Taken from https://eonet.gsfc.nasa.gov/api/v3/categories. Kept as a fixed list so
# the app can start and seed itself even without a working internet connection.
EONET_CATEGORIES = [
    ("drought", "Drought"),
    ("dustHaze", "Dust and Haze"),
    ("earthquakes", "Earthquakes"),
    ("floods", "Floods"),
    ("landslides", "Landslides"),
    ("manmade", "Manmade"),
    ("seaLakeIce", "Sea and Lake Ice"),
    ("severeStorms", "Severe Storms"),
    ("snow", "Snow"),
    ("tempExtremes", "Temperature Extremes"),
    ("volcanoes", "Volcanoes"),
    ("waterColor", "Water Color"),
    ("wildfires", "Wildfires"),
]


def get_db():
    connection = sqlite3.connect(DB_PATH)
    # Lets each row be read by column name, for example row["title"].
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watched_events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            eonet_id     TEXT    NOT NULL UNIQUE,
            title        TEXT    NOT NULL,
            category     TEXT,
            status       TEXT,
            latitude     REAL,
            longitude    REAL,
            event_date   TEXT,
            magnitude    REAL,
            mag_unit     TEXT,
            source_url   TEXT,
            note         TEXT    DEFAULT '',
            alert_active INTEGER DEFAULT 0,
            saved_at     TEXT    DEFAULT (datetime('now'))
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            slug  TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text  TEXT,
            searched_at TEXT DEFAULT (datetime('now'))
        );
    """)

    connection.commit()
    connection.close()


def seed_categories():
    connection = get_db()
    cursor = connection.cursor()

    # slug is UNIQUE, so OR IGNORE quietly skips any category that is already
    # stored rather than failing every time the app restarts.
    for slug, label in EONET_CATEGORIES:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (slug, label) VALUES (?, ?)",
            (slug, label)
        )

    connection.commit()
    connection.close()


def get_categories():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT slug, label FROM categories ORDER BY label;")
    categories = cursor.fetchall()
    connection.close()
    return categories


def get_saved_eonet_ids():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT eonet_id FROM watched_events;")
    rows = cursor.fetchall()
    connection.close()

    saved_ids = []
    for row in rows:
        saved_ids.append(row["eonet_id"])
    return saved_ids


def get_watched_events():
    """Read the watch list and turn each row back into a WatchedEvent object.

    The database row id is kept next to the object because the remove and note
    pages need it, while the object itself only knows the EONET id.
    """
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM watched_events ORDER BY saved_at DESC, id DESC;")
    rows = cursor.fetchall()
    connection.close()

    saved_events = []
    for row in rows:
        event = WatchedEvent(
            row["eonet_id"],
            row["title"],
            row["category"],
            row["status"],
            row["latitude"],
            row["longitude"],
            row["event_date"],
            row["magnitude"],
            row["mag_unit"],
            row["source_url"],
            note=row["note"],
            alert_active=bool(row["alert_active"]),
        )
        saved_events.append({"id": row["id"], "event": event})
    return saved_events


# Run on import so the database is ready before the first request is handled.
init_db()
seed_categories()

app = Flask(__name__)
# Flask needs a secret key before flash() can store messages in the session.
app.secret_key = "nasa-natural-events-tracker"

fetcher = EventFetcher()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/browse")
def browse():
    category = request.args.get("category", "")
    status = request.args.get("status", "open")

    # The form sends days as text, so fall back to 30 if it is empty or not a number.
    days_text = request.args.get("days", "30")
    if days_text.isdigit() and int(days_text) > 0:
        days = int(days_text)
    else:
        days = 30

    # An empty dropdown choice means "all categories", so no category is sent to the API.
    if category == "":
        category_for_api = None
    else:
        category_for_api = category

    events = []
    error_message = None
    try:
        events = fetcher.fetch_events(status=status, category=category_for_api, days=days, limit=50)
    except RequestException:
        error_message = "Could not reach the NASA EONET API. Please check your internet connection and try again."

    return render_template(
        "browse.html",
        events=events,
        categories=get_categories(),
        category=category,
        status=status,
        days=days,
        error_message=error_message,
        saved_ids=get_saved_eonet_ids(),
    )


@app.route("/event/<eonet_id>")
def event_detail(eonet_id):
    event = None
    error_message = None
    try:
        event = fetcher.fetch_event(eonet_id)
    except RequestException:
        # EONET answers with an error status for an unknown id, so a failure here can
        # mean either a bad id or a network problem.
        error_message = "Could not load this event. The event ID may not exist, or the NASA EONET API may be unavailable."

    is_saved = False
    if event is not None:
        is_saved = event.get_eonet_id() in get_saved_eonet_ids()

    return render_template(
        "event_detail.html",
        event=event,
        error_message=error_message,
        is_saved=is_saved,
    )


@app.route("/watchlist")
def watchlist():
    return render_template("watchlist.html", saved_events=get_watched_events())


@app.route("/watch/add/<eonet_id>", methods=["POST"])
def watch_add(eonet_id):
    try:
        event = fetcher.fetch_event(eonet_id)
    except RequestException:
        flash("Could not add that event because the NASA EONET API could not be reached.")
        return redirect(url_for("browse"))

    connection = get_db()
    cursor = connection.cursor()
    # eonet_id is UNIQUE, so OR IGNORE means adding the same event twice does not
    # create a second row and does not raise an error.
    cursor.execute("""
        INSERT OR IGNORE INTO watched_events
            (eonet_id, title, category, status, latitude, longitude,
             event_date, magnitude, mag_unit, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        event.get_eonet_id(),
        event.title,
        event.category,
        event.status,
        event.latitude,
        event.longitude,
        event.event_date,
        event.magnitude,
        event.mag_unit,
        event.source_url,
    ))
    was_added = cursor.rowcount == 1
    connection.commit()
    connection.close()

    if was_added:
        flash(f"Added {event.title} to your watch list.")
    else:
        flash(f"{event.title} is already in your watch list.")

    return redirect(url_for("watchlist"))


@app.route("/watch/remove/<int:row_id>", methods=["POST"])
def watch_remove(row_id):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT title FROM watched_events WHERE id = ?;", (row_id,))
    row = cursor.fetchone()
    cursor.execute("DELETE FROM watched_events WHERE id = ?;", (row_id,))
    connection.commit()
    connection.close()

    if row is None:
        flash("That event was not in your watch list.")
    else:
        flash(f"Removed {row['title']} from your watch list.")

    return redirect(url_for("watchlist"))


@app.route("/watch/note/<int:row_id>", methods=["GET", "POST"])
def watch_note(row_id):
    if request.method == "POST":
        note = request.form.get("note", "")
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("UPDATE watched_events SET note = ? WHERE id = ?;", (note, row_id))
        connection.commit()
        connection.close()

        flash("Note saved.")
        return redirect(url_for("watchlist"))

    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id, title, note FROM watched_events WHERE id = ?;", (row_id,))
    saved = cursor.fetchone()
    connection.close()

    if saved is None:
        flash("That event is not in your watch list.")
        return redirect(url_for("watchlist"))

    return render_template("edit_note.html", saved=saved)
