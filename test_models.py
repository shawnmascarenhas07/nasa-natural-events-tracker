"""Checks the classes in models.py and confirms the EONET API is reachable.

Run it with:  python test_models.py
"""

from models import NaturalEvent, WatchedEvent, EventFetcher


def make_open_event():
    return NaturalEvent("EONET_1", "Wildfire - British Columbia", "Wildfires", "open",
                        51.3, -122.5, "2024-08-12", None, None, "https://example.com")


def make_closed_event():
    return NaturalEvent("EONET_2", "Storm - Atlantic", "Severe Storms", "closed",
                        18.1, -131.8, "2024-07-01", 35.0, "kts", "https://example.com")


def test_is_active():
    print("is_active()")
    open_event = make_open_event()
    closed_event = make_closed_event()

    assert open_event.is_active() is True
    assert closed_event.is_active() is False

    print("   open event  ->", open_event.is_active())
    print("   closed event ->", closed_event.is_active())


def test_summary():
    print("summary()")
    event = make_open_event()
    text = event.summary()

    assert len(text) > 0
    assert event.category in text
    assert event.title in text
    assert event.status in text

    print("  ", text)


def test_encapsulation():
    print("private attribute and getter")
    event = make_open_event()

    assert event.get_eonet_id() == "EONET_1"
    print("   get_eonet_id() ->", event.get_eonet_id())

    try:
        print(event.__eonet_id)
        print("   PROBLEM: the private attribute was readable from outside")
    except AttributeError:
        print("   reading event.__eonet_id from outside raises AttributeError, as expected")


def test_toggle_alert():
    print("toggle_alert()")
    watched = WatchedEvent("EONET_1", "Wildfire - British Columbia", "Wildfires", "open",
                           51.3, -122.5, "2024-08-12", None, None, "https://example.com")

    assert watched.alert_active is False
    assert watched.toggle_alert() is True
    assert watched.alert_active is True
    assert watched.toggle_alert() is False

    print("   False -> True -> False, and the new value is returned each time")


def test_watched_summary():
    print("WatchedEvent.summary() extends the parent version")
    watched = WatchedEvent("EONET_1", "Wildfire - British Columbia", "Wildfires", "open",
                           51.3, -122.5, "2024-08-12", None, None, "https://example.com",
                           note="Near a friend's town")
    watched.toggle_alert()
    text = watched.summary()

    assert "Wildfires" in text
    assert "Near a friend's town" in text
    assert "alert on" in text

    print("  ", text)


def test_fetch_events(fetcher):
    print("fetch_events() against the live API")
    events = fetcher.fetch_events(status="open", days=60, limit=20)

    assert len(events) > 0
    for event in events:
        assert isinstance(event, NaturalEvent)

    print(f"   received {len(events)} events, showing the first 5:")
    for event in events[:5]:
        print("    -", event.summary())
        print("      date:", event.event_date,
              "| lat:", event.latitude,
              "| lon:", event.longitude)
    return events


def test_fetch_event(fetcher, events):
    print("fetch_event() against the live API")
    wanted_id = events[0].get_eonet_id()
    event = fetcher.fetch_event(wanted_id)

    assert isinstance(event, NaturalEvent)
    assert event.get_eonet_id() == wanted_id

    print("   asked for", wanted_id, "and received one NaturalEvent")
    print("  ", event.summary())
    print("   source:", event.source_url)


def test_magnitude(events):
    print("magnitude is read from the geometry entry")
    with_magnitude = None
    without_magnitude = None
    for event in events:
        if event.magnitude is not None and with_magnitude is None:
            with_magnitude = event
        if event.magnitude is None and without_magnitude is None:
            without_magnitude = event

    if with_magnitude:
        print(f"   {with_magnitude.title} -> {with_magnitude.magnitude} {with_magnitude.mag_unit}")
    else:
        print("   no event in this batch reported a magnitude")

    if without_magnitude:
        print(f"   {without_magnitude.title} -> magnitude is None, handled without crashing")
    else:
        print("   every event in this batch reported a magnitude")


def main():
    print("=== Offline checks (Group A3) ===")
    test_is_active()
    test_summary()
    test_encapsulation()
    test_toggle_alert()
    test_watched_summary()

    print()
    print("=== Live API checks (Group B1) ===")
    fetcher = EventFetcher()
    events = test_fetch_events(fetcher)
    test_fetch_event(fetcher, events)
    test_magnitude(events)

    print()
    print("All checks passed.")


if __name__ == "__main__":
    main()
