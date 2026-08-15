"""Classes used by the NASA Natural Events Tracker."""

import requests


class NaturalEvent:
    """A single natural event as described by the EONET API."""

    def __init__(self, eonet_id, title, category, status, latitude, longitude,
                 event_date, magnitude, mag_unit, source_url):
        # The EONET id identifies the event, so it is kept private and read through a getter.
        self.__eonet_id = eonet_id
        self.title = title
        self.category = category
        self.status = status
        self.latitude = latitude
        self.longitude = longitude
        self.event_date = event_date
        self.magnitude = magnitude
        self.mag_unit = mag_unit
        self.source_url = source_url

    def get_eonet_id(self):
        return self.__eonet_id

    def is_active(self):
        return self.status == "open"

    def summary(self):
        return f"{self.category}: {self.title} ({self.status})"


class WatchedEvent(NaturalEvent):
    """An event the user has saved to the watch list."""

    def __init__(self, eonet_id, title, category, status, latitude, longitude,
                 event_date, magnitude, mag_unit, source_url, note="", alert_active=False):
        super().__init__(eonet_id, title, category, status, latitude, longitude,
                         event_date, magnitude, mag_unit, source_url)
        self.note = note
        self.alert_active = alert_active

    def toggle_alert(self):
        self.alert_active = not self.alert_active
        return self.alert_active

    def summary(self):
        text = super().summary()
        if self.note:
            text = text + f" - note: {self.note}"
        if self.alert_active:
            text = text + " - alert on"
        else:
            text = text + " - alert off"
        return text


class EventFetcher:
    """Handles every request to the EONET API."""

    BASE = "https://eonet.gsfc.nasa.gov/api/v3"

    def __init__(self, timeout=10):
        self.timeout = timeout

    def fetch_events(self, status="open", category=None, days=30, limit=50):
        params = {"status": status, "days": days, "limit": limit}
        if category:
            params["category"] = category

        response = requests.get(f"{self.BASE}/events", params=params, timeout=self.timeout)
        response.raise_for_status()

        events = []
        for raw in response.json()["events"]:
            events.append(self.build_event(raw))
        return events

    def fetch_event(self, eonet_id):
        response = requests.get(f"{self.BASE}/events/{eonet_id}", timeout=self.timeout)
        response.raise_for_status()

        # This endpoint returns the event on its own, without the "events" list
        # that the /events endpoint wraps its results in.
        return self.build_event(response.json())

    def build_event(self, raw):
        """Turn one raw event dictionary from the API into a NaturalEvent object."""
        categories = raw.get("categories") or []
        if categories:
            category = categories[0]["title"]
        else:
            category = "Unknown"

        # "closed" is null while an event is still running and holds a date once it has ended.
        if raw.get("closed"):
            status = "closed"
        else:
            status = "open"

        sources = raw.get("sources") or []
        if sources:
            source_url = sources[0]["url"]
        else:
            source_url = None

        latitude = None
        longitude = None
        event_date = None
        magnitude = None
        mag_unit = None

        geometry = raw.get("geometry") or []
        if geometry:
            first = geometry[0]

            date_text = first.get("date")
            if date_text:
                event_date = date_text[:10]

            # EONET stores magnitude inside the geometry entry, not on the event itself,
            # and many events have no magnitude at all.
            magnitude = first.get("magnitudeValue")
            mag_unit = first.get("magnitudeUnit")

            # Point coordinates are [longitude, latitude]. Polygon events cover an area
            # rather than one spot, so they are stored without coordinates.
            if first.get("type") == "Point":
                coordinates = first.get("coordinates") or []
                if len(coordinates) == 2:
                    longitude = coordinates[0]
                    latitude = coordinates[1]

        return NaturalEvent(
            raw.get("id"),
            raw.get("title"),
            category,
            status,
            latitude,
            longitude,
            event_date,
            magnitude,
            mag_unit,
            source_url,
        )
