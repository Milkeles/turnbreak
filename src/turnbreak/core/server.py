from __future__ import annotations

import json
import queue
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from turnbreak.core.actions import read_item
from turnbreak.core.config import load_config
from turnbreak.core.items import Item, item_payload, load_list, select_item
from turnbreak.core.notify import notify_native
from turnbreak.core.state import load_state, save_state

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


class BrowseHistory:
    """Tracks, per session, the ordered locators a reader has stepped
    through with Next/Previous, purely in server memory.

    Deliberately not persisted to state.json -- browse position is a
    scroll-back convenience for the current server process, not part of
    the durable record the way shown_locator is. A restart loses it,
    which just means Previous has nothing to go back to yet; Next still
    works by picking a fresh item.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._history: dict[str, list[str]] = {}
        self._index: dict[str, int] = {}

    def record(self, session_id: str, locator: str) -> None:
        """Note that `locator` is now on screen for this session.

        A no-op if it's already the current entry, so re-recording the
        item that's already showing (the self-heal step in
        _handle_action) never duplicates it or drops forward history.
        """
        with self._lock:
            history = self._history.setdefault(session_id, [])
            index = self._index.get(session_id, -1)
            if 0 <= index < len(history) and history[index] == locator:
                return
            del history[index + 1 :]
            history.append(locator)
            self._index[session_id] = len(history) - 1

    def move(self, session_id: str, delta: int) -> str | None:
        """Step forward or backward through a session's history.

        Returns None past either edge, so the caller knows whether to
        fall back to selecting a fresh item (Next) or simply do nothing
        (Previous with nothing further back).
        """
        with self._lock:
            history = self._history.get(session_id, [])
            index = self._index.get(session_id, -1) + delta
            if index < 0 or index >= len(history):
                return None
            self._index[session_id] = index
            return history[index]

    def snapshot(self, session_id: str) -> set[str]:
        with self._lock:
            return set(self._history.get(session_id, []))


def _select_next(
    session_id: str, *, exclude: set[str] | None = None
) -> tuple[str, dict[str, object], str]:
    """Pick whatever the reader should see next from the current list.

    Shared by _handle_action (to push it live the instant Read is
    clicked, or Next runs out of browse history, rather than leaving a
    stale item on screen until the next agent turn fires) and
    _serve_current's fallback (so a reload doesn't show a blank
    "waiting" page just because the previously shown item is no longer
    in the list). Never refills the list itself -- that's fire.py's job,
    tied to agent turn boundaries.
    """
    config = load_config()
    entries = load_list()
    entry = select_item(
        entries, config.target_read_minutes, config.words_per_minute, exclude=exclude
    )
    if entry is None:
        return "end", {}, ""
    payload = item_payload(entry.item, session_id, config.words_per_minute)
    return "item", payload, entry.item.locator


def _find_item(locator: str) -> Item | None:
    for entry in load_list():
        if entry.item.locator == locator:
            return entry.item
    return None


def _make_handler(broker: Broker) -> type[BaseHTTPRequestHandler]:
    history = BrowseHistory()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._serve_page()
            elif self.path == "/events":
                self._serve_events()
            elif self.path == "/status":
                self._respond_json({"clients": broker.client_count()})
            elif self.path == "/current":
                self._serve_current()
            elif self.path.startswith("/pdf?") or self.path == "/pdf":
                self._serve_pdf()
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
            elif self.path == "/end":
                self._handle_end(payload)
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

        def _serve_current(self) -> None:
            """What a fresh page load (new tab, reload, or a reconnect after the
            server restarted) should show immediately, before any live event
            arrives. Reconstructed from state.json + list.jsonl rather than
            cached in the broker, since the broker only remembers connected
            clients and forgets every broadcast the instant it's sent.
            """
            session = load_state()
            if session is None or session.shown_locator is None:
                self._respond_json({"status": "waiting"})
                return
            if session.shown_locator == "":
                # session_id rides along so a reload at end-of-list still
                # lets the page send Previous -- BrowseHistory keyed on it
                # survives in server memory even though shown_locator itself
                # carries no locator to anchor a self-heal record on.
                self._respond_json({"status": "end", "session_id": session.session_id})
                return
            config = load_config()
            for entry in load_list():
                if entry.item.locator == session.shown_locator:
                    payload = item_payload(entry.item, session.session_id, config.words_per_minute)
                    self._respond_json({"status": "item", "item": payload})
                    return
            # The previously shown item is gone (read or skipped) but
            # nothing pushed a replacement -- e.g. it was resolved while
            # no tab was connected to receive the live broadcast. Serve
            # whatever's next now rather than leaving the reader looking
            # at "waiting" with unread items still sitting in the list.
            status, item, _ = _select_next(session.session_id)
            if status == "item":
                self._respond_json({"status": "item", "item": item})
            else:
                self._respond_json({"status": "end", "session_id": session.session_id})

        def _serve_pdf(self) -> None:
            """Stream a folder-mode PDF straight from disk.

            The browser's own PDF viewer requests this like any other PDF
            URL, so there's no base64 blow-up in list.jsonl and no size
            cap needed — the file is read once, on demand, rather than
            embedded in every refill. Only locators already present in
            list.jsonl as PDFs are servable, so this can't be used to read
            arbitrary files off disk via the locator query param.
            """
            query = parse_qs(urlparse(self.path).query)
            locator = query.get("locator", [""])[0]
            known = {entry.item.locator for entry in load_list() if entry.item.is_pdf}
            if locator not in known or not Path(locator).is_file():
                self.send_error(404)
                return
            body = Path(locator).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
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
            session_id = payload.get("session_id")
            locator = payload.get("locator")
            if isinstance(session_id, str) and isinstance(locator, str):
                # fire.py pushes items from a separate process (the agent
                # hook), so this is the only place an agent-driven item
                # ever reaches the running server. Recording it here keeps
                # Next/Previous aware of it too.
                history.record(session_id, locator)
            self._respond_json({"ok": True, "needs_tab": needs_tab})

        def _handle_end(self, payload: dict[str, object]) -> None:
            needs_tab = broker.client_count() == 0
            broker.broadcast("end", {})
            self._respond_json({"ok": True, "needs_tab": needs_tab})

        def _handle_done(self, payload: dict[str, object]) -> None:
            broker.broadcast("done", payload)
            notify_native()
            self._respond_json({"ok": True})

        def _handle_action(self, payload: dict[str, object]) -> None:
            action = payload.get("action")
            session_id = payload.get("session_id")
            locator = payload.get("locator")
            if isinstance(session_id, str) and isinstance(locator, str):
                if action == "read":
                    read_item(session_id, locator)
                    self._advance(session_id, exclude=set())
                elif action in ("next", "previous"):
                    # Self-heal: a fresh server process or a page reload
                    # means `history` may never have heard about the item
                    # currently on screen. Recording it here (a no-op if
                    # already the current entry) guarantees Next/Previous
                    # always has a correct anchor to step from. Skipped
                    # when locator is empty -- that's the page asking for
                    # Previous from end-of-list, where there's no on-screen
                    # item to anchor on, and recording "" would corrupt the
                    # history it's trying to step back through.
                    if locator:
                        history.record(session_id, locator)
                    self._step(session_id, delta=1 if action == "next" else -1)
            self._respond_json({"ok": True})

        def _advance(self, session_id: str, *, exclude: set[str]) -> None:
            """Show whatever's next after the on-screen item stops being
            relevant, instead of leaving it on screen until the next
            agent turn happens to fire() -- which, outside an active
            turn, may be minutes away or never.
            """
            status, item, shown_locator = _select_next(session_id, exclude=exclude)
            broker.broadcast(status, item)
            if status == "item":
                history.record(session_id, shown_locator)
            session = load_state()
            if session is not None and session.session_id == session_id:
                save_state(replace(session, shown_locator=shown_locator))

        def _step(self, session_id: str, *, delta: int) -> None:
            """Move through browse history for Next (delta=1) or Previous
            (delta=-1). Retraces already-seen items when they're still
            available rather than picking a fresh one, so Previous then
            Next lands back where you were. Next falls back to a fresh
            pending item, excluding everything already browsed this
            session, once history runs out; Previous simply does nothing
            once there's nothing further back.
            """
            locator = history.move(session_id, delta)
            item = _find_item(locator) if locator is not None else None
            if item is not None:
                config = load_config()
                broker.broadcast("item", item_payload(item, session_id, config.words_per_minute))
                session = load_state()
                if session is not None and session.session_id == session_id:
                    save_state(replace(session, shown_locator=item.locator))
            elif delta > 0:
                self._advance(session_id, exclude=history.snapshot(session_id))

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
