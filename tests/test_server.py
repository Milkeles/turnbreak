from __future__ import annotations

import http.client
import inspect
import json
import threading
import time

import pytest

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
