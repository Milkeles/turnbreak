from __future__ import annotations

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from turnbreak.core.notify import notify_native

_PAGE_PATH = Path(__file__).resolve().parent.parent / "page" / "index.html"
_HEARTBEAT_SECONDS = 15.0


class Broker:
    """Tracks connected SSE clients and fans out events to all of them."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clients: set[queue.Queue[str]] = set()

    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def subscribe(self) -> queue.Queue[str]:
        client: queue.Queue[str] = queue.Queue()
        with self._lock:
            self._clients.add(client)
        return client

    def unsubscribe(self, client: queue.Queue[str]) -> None:
        with self._lock:
            self._clients.discard(client)

    def broadcast(self, event: str, data: dict[str, object]) -> None:
        message = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        with self._lock:
            clients = list(self._clients)
        for client in clients:
            client.put(message)


def _make_handler(broker: Broker) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._serve_page()
            elif self.path == "/events":
                self._serve_events()
            elif self.path == "/status":
                self._respond_json({"clients": broker.client_count()})
            else:
                self.send_error(404)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                self.send_error(400)
                return
            if self.path == "/item":
                self._handle_item(payload)
            elif self.path == "/done":
                self._handle_done(payload)
            elif self.path == "/action":
                self._handle_action(payload)
            else:
                self.send_error(404)

        def _serve_page(self) -> None:
            body = _PAGE_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _serve_events(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            client = broker.subscribe()
            try:
                while True:
                    try:
                        message = client.get(timeout=_HEARTBEAT_SECONDS)
                    except queue.Empty:
                        message = ": keep-alive\n\n"
                    self.wfile.write(message.encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                broker.unsubscribe(client)

        def _handle_item(self, payload: dict[str, object]) -> None:
            needs_tab = broker.client_count() == 0
            broker.broadcast("item", payload)
            self._respond_json({"ok": True, "needs_tab": needs_tab})

        def _handle_done(self, payload: dict[str, object]) -> None:
            broker.broadcast("done", payload)
            notify_native()
            self._respond_json({"ok": True})

        def _handle_action(self, payload: dict[str, object]) -> None:
            # Seam for P3: Read/Skip/Keep reading have no effect yet.
            self._respond_json({"ok": True})

        def _respond_json(self, data: dict[str, object]) -> None:
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    return Handler


class TurnbreakServer(ThreadingHTTPServer):
    broker: Broker
    daemon_threads = True


def create_server(port: int) -> TurnbreakServer:
    broker = Broker()
    server = TurnbreakServer(("127.0.0.1", port), _make_handler(broker))
    server.broker = broker
    return server


def serve_forever(port: int) -> None:
    server: TurnbreakServer = create_server(port)
    try:
        server.serve_forever()
    finally:
        server.server_close()
