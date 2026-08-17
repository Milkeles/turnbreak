from __future__ import annotations

import http.client
import inspect
import json
import queue
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest

from turnbreak.core import state
from turnbreak.core.items import Item, ListEntry, history_locators, load_list, save_list
from turnbreak.core.server import Broker, create_server


def test_create_server_binds_loopback_only():
    server = create_server(0)
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


def test_create_server_has_no_host_parameter():
    assert list(inspect.signature(create_server).parameters) == ["port"]


def test_broker_broadcast_delivers_to_subscribers():
    broker = Broker()
    client = broker.subscribe()
    broker.broadcast("item", {"title": "Example"})
    message = client.get(timeout=1)
    assert "event: item" in message
    assert "Example" in message


def test_broker_client_count_tracks_subscriptions():
    broker = Broker()
    assert broker.client_count() == 0
    client = broker.subscribe()
    assert broker.client_count() == 1
    broker.unsubscribe(client)
    assert broker.client_count() == 0


@pytest.fixture
def running_server():
    server = create_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _post(port: int, path: str, payload: dict) -> dict:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        body = json.dumps(payload).encode()
        conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        return json.loads(response.read())
    finally:
        conn.close()


def test_post_item_reports_needs_tab_when_no_clients(running_server):
    port = running_server.server_address[1]
    result = _post(port, "/item", {"title": "Example"})
    assert result == {"ok": True, "needs_tab": True}


def test_post_item_reports_tab_present_when_client_connected(running_server):
    running_server.broker.subscribe()
    port = running_server.server_address[1]
    result = _post(port, "/item", {"title": "Example"})
    assert result == {"ok": True, "needs_tab": False}


def test_post_end_reports_needs_tab_when_no_clients(running_server):
    port = running_server.server_address[1]
    result = _post(port, "/end", {})
    assert result == {"ok": True, "needs_tab": True}


def test_post_end_broadcasts_end_event(running_server):
    port = running_server.server_address[1]
    client = running_server.broker.subscribe()
    _post(port, "/end", {})
    message = client.get(timeout=1)
    assert "event: end" in message


def test_post_done_broadcasts_and_responds_ok(running_server):
    port = running_server.server_address[1]
    result = _post(port, "/done", {"session_id": "abc"})
    assert result == {"ok": True}


def test_status_reports_client_count(running_server):
    port = running_server.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("GET", "/status")
    response = conn.getresponse()
    assert json.loads(response.read()) == {"clients": 0}
    conn.close()


def test_get_page_serves_html(running_server):
    port = running_server.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("GET", "/")
    response = conn.getresponse()
    body = response.read()
    assert response.status == 200
    assert b"<html" in body
    conn.close()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def test_post_action_read_marks_item_read(running_server, home):
    save_list([ListEntry(Item("A", "https://a", 100, "curated"))])
    state.start_turn("abc", 0.0)
    port = running_server.server_address[1]

    result = _post(port, "/action", {"action": "read", "session_id": "abc", "locator": "https://a"})

    assert result == {"ok": True}
    assert load_list()[0].status == "read"
    assert history_locators() == {"https://a"}


def test_post_action_read_broadcasts_the_next_item_live(running_server, home):
    """Read must not leave the just-resolved item on screen until the
    next agent turn happens to fire() -- the reader clicked precisely
    because they want to see what's next, right now.
    """
    save_list(
        [
            ListEntry(Item("A", "https://a", 100, "curated")),
            ListEntry(Item("B", "https://b", 100, "curated")),
        ]
    )
    state.start_turn("abc", 0.0)
    client = running_server.broker.subscribe()
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "read", "session_id": "abc", "locator": "https://a"})

    message = client.get(timeout=1)
    assert "event: item" in message
    assert "https://b" in message
    assert state.load_state().shown_locator == "https://b"


def test_post_action_read_broadcasts_end_when_nothing_is_left(running_server, home):
    save_list([ListEntry(Item("A", "https://a", 100, "curated"))])
    state.start_turn("abc", 0.0)
    client = running_server.broker.subscribe()
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "read", "session_id": "abc", "locator": "https://a"})

    message = client.get(timeout=1)
    assert "event: end" in message
    assert state.load_state().shown_locator == ""


def test_post_action_ignores_shown_locator_from_a_different_session(running_server, home):
    save_list([ListEntry(Item("A", "https://a", 100, "curated"))])
    started = state.start_turn("other-session", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "read", "session_id": "abc", "locator": "https://a"})

    assert state.load_state().shown_locator == "https://a"


def test_post_action_next_shows_a_different_pending_item_live_without_resolving_the_current_one(
    running_server, home
):
    save_list(
        [
            ListEntry(Item("A", "https://a", 100, "curated")),
            ListEntry(Item("B", "https://b", 100, "curated")),
        ]
    )
    state.start_turn("abc", 0.0)
    client = running_server.broker.subscribe()
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "next", "session_id": "abc", "locator": "https://a"})

    message = client.get(timeout=1)
    assert "event: item" in message
    assert "https://b" in message
    assert state.load_state().shown_locator == "https://b"
    assert {entry.item.locator for entry in load_list()} == {"https://a", "https://b"}
    assert history_locators() == set()


def test_post_action_next_broadcasts_end_when_nothing_else_is_pending(running_server, home):
    save_list([ListEntry(Item("A", "https://a", 100, "curated"))])
    state.start_turn("abc", 0.0)
    client = running_server.broker.subscribe()
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "next", "session_id": "abc", "locator": "https://a"})

    message = client.get(timeout=1)
    assert "event: end" in message


def test_post_action_previous_is_a_noop_with_nothing_before_the_current_item(running_server, home):
    port = running_server.server_address[1]
    client = running_server.broker.subscribe()
    _post(port, "/item", {"session_id": "abc", "locator": "https://a", "title": "A"})
    client.get(timeout=1)

    _post(port, "/action", {"action": "previous", "session_id": "abc", "locator": "https://a"})

    with pytest.raises(queue.Empty):
        client.get(timeout=0.2)


def test_post_action_previous_then_next_retraces_history_instead_of_picking_something_new(
    running_server, home
):
    save_list(
        [
            ListEntry(Item("A", "https://a", 100, "curated")),
            ListEntry(Item("B", "https://b", 100, "curated")),
            ListEntry(Item("C", "https://c", 100, "curated")),
        ]
    )
    state.start_turn("abc", 0.0)
    client = running_server.broker.subscribe()
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "next", "session_id": "abc", "locator": "https://a"})
    client.get(timeout=1)  # B shown
    _post(port, "/action", {"action": "previous", "session_id": "abc", "locator": "https://b"})
    client.get(timeout=1)  # A shown again
    _post(port, "/action", {"action": "next", "session_id": "abc", "locator": "https://a"})
    message = client.get(timeout=1)

    assert "https://b" in message
    assert "https://c" not in message


def test_post_action_previous_with_no_locator_steps_back_after_next_reaches_the_end(
    running_server, home
):
    """Regression test: once Next has been clicked through to end-of-list,
    the page has no current item to anchor a locator on, so it sends
    Previous with an empty locator. The server must still walk browse
    history back instead of doing nothing.

    The failed forward move never advances BrowseHistory's index past B
    (only real items get recorded), so from history's point of view the
    reader is still "at" B when end-of-list is shown -- exactly like a
    browser's forward button refusing to move past the last page. The
    first Previous therefore steps to A, same as pressing back from B
    would anywhere else.
    """
    save_list(
        [
            ListEntry(Item("A", "https://a", 100, "curated")),
            ListEntry(Item("B", "https://b", 100, "curated")),
        ]
    )
    state.start_turn("abc", 0.0)
    client = running_server.broker.subscribe()
    port = running_server.server_address[1]

    _post(port, "/action", {"action": "next", "session_id": "abc", "locator": "https://a"})
    client.get(timeout=1)  # B shown
    _post(port, "/action", {"action": "next", "session_id": "abc", "locator": "https://b"})
    message = client.get(timeout=1)
    assert "event: end" in message

    _post(port, "/action", {"action": "previous", "session_id": "abc", "locator": ""})
    message = client.get(timeout=1)

    assert "event: item" in message
    assert "https://a" in message
    assert state.load_state().shown_locator == "https://a"


def _get(port: int, path: str) -> dict:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        return json.loads(response.read())
    finally:
        conn.close()


def test_current_reports_waiting_when_no_state_recorded(running_server, home):
    port = running_server.server_address[1]
    assert _get(port, "/current") == {"status": "waiting"}


def test_current_reports_waiting_when_no_item_has_been_shown_yet(running_server, home):
    state.start_turn("abc", 0.0)
    port = running_server.server_address[1]
    assert _get(port, "/current") == {"status": "waiting"}


def test_current_reconstructs_the_last_shown_item(running_server, home):
    item = Item("A", "https://a", 460, "curated", body="hello")
    save_list([ListEntry(item)])
    started = state.start_turn("abc", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))
    port = running_server.server_address[1]

    result = _get(port, "/current")

    assert result == {
        "status": "item",
        "item": {
            "session_id": "abc",
            "locator": "https://a",
            "title": "A",
            "source": "curated",
            "read_minutes": 2,
            "body": "hello",
            "is_pdf": False,
        },
    }


def test_current_reports_end_when_the_list_was_exhausted(running_server, home):
    started = state.start_turn("abc", 0.0)
    state.save_state(replace(started, shown_locator=""))
    port = running_server.server_address[1]

    assert _get(port, "/current") == {"status": "end", "session_id": "abc"}


def _get_raw(port: int, path: str) -> http.client.HTTPResponse:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("GET", path)
    return conn.getresponse()


def test_pdf_streams_a_known_pdf_locator(running_server, home, tmp_path):
    pdf_path = tmp_path / "book.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake bytes")
    save_list([ListEntry(Item("Book", str(pdf_path), 100, "folder", is_pdf=True))])
    port = running_server.server_address[1]

    response = _get_raw(port, "/pdf?locator=" + str(pdf_path))

    assert response.status == 200
    assert response.getheader("Content-Type") == "application/pdf"
    assert response.read() == b"%PDF-1.4 fake bytes"


def test_pdf_404s_for_a_locator_not_in_the_list(running_server, home, tmp_path):
    pdf_path = tmp_path / "book.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake bytes")
    port = running_server.server_address[1]

    response = _get_raw(port, "/pdf?locator=" + str(pdf_path))

    assert response.status == 404


def test_pdf_404s_for_a_non_pdf_item_even_if_listed(running_server, home, tmp_path):
    text_path = tmp_path / "article.txt"
    text_path.write_text("hello")
    save_list([ListEntry(Item("Article", str(text_path), 100, "folder", is_pdf=False))])
    port = running_server.server_address[1]

    response = _get_raw(port, "/pdf?locator=" + str(text_path))

    assert response.status == 404


def test_current_reports_end_when_the_shown_item_is_gone_and_nothing_else_is_pending(
    running_server, home
):
    started = state.start_turn("abc", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))
    port = running_server.server_address[1]

    assert _get(port, "/current") == {"status": "end", "session_id": "abc"}


def test_current_serves_the_next_pending_item_when_the_shown_one_is_gone(running_server, home):
    next_item = Item("Next", "https://b", 100, "curated")
    save_list([ListEntry(next_item)])
    started = state.start_turn("abc", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))
    port = running_server.server_address[1]

    result = _get(port, "/current")

    assert result["status"] == "item"
    assert result["item"]["locator"] == "https://b"


def test_events_stream_delivers_broadcast_item(running_server):
    port = running_server.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("GET", "/events")
    response = conn.getresponse()

    def post_item():
        time.sleep(0.05)
        _post(port, "/item", {"title": "Example"})

    poster = threading.Thread(target=post_item)
    poster.start()
    poster.join()

    chunk = response.fp.read1(200)
    assert b"event: item" in chunk
    assert b"Example" in chunk
    conn.close()
