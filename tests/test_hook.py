import importlib.util
from pathlib import Path

# Load the hook script directly by path to avoid relying on it being
# importable as a package in every test environment.
_hook_path = (
    Path(__file__).resolve().parent.parent / "src" / "turnbreak" / "adapters" / "turnbreak-hook.py"
)
_spec = importlib.util.spec_from_file_location("turnbreak_hook", str(_hook_path))
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def test_detect_event_start_and_end():
    assert hook._detect_event({"UserPromptSubmit": {}}) == "start"
    assert hook._detect_event({"Stop": {}}) == "end"
    assert hook._detect_event({"some": "BeforeAgent"}) == "start"
    assert hook._detect_event({"nested": {"ev": "AfterAgent"}}) == "end"


def test_main_calls_turnbreak_and_writes_session_file(tmp_path, capsys, monkeypatch):
    # Use tmp config dir
    monkeypatch.setattr(hook, "config_dir", lambda: tmp_path)
    called = {}

    def fake_call(args):
        called["args"] = args
        return 0

    payload = {"UserPromptSubmit": {"prompt": "hi"}}
    out = hook.main(payload, call_turnbreak=fake_call, argv=[])
    assert out == {"ok": True}
    assert "args" in called and called["args"][0] == "start"
    # session file created
    assert (tmp_path / "hook_last_session").exists()

    # Now simulate end event using recorded session id
    called.clear()
    out2 = hook.main({"Stop": {}}, call_turnbreak=fake_call, argv=[])
    assert out2 == {"ok": True}
    assert "args" in called and called["args"][0] == "stop"


def test_hint_event_takes_priority_over_payload_sniffing():
    assert hook._hint_event(["--hint", "start"]) == "start"
    assert hook._hint_event(["--hint", "end"]) == "end"
    assert hook._hint_event([]) is None
    assert hook._hint_event(["--hint"]) is None
    assert hook._hint_event(["--hint", "bogus"]) is None


def test_main_uses_hint_for_copilot_payload_shape(tmp_path, monkeypatch):
    """Copilot's real hook payload has no event name in it at all, unlike
    the other three agents; --hint is how the hooks.json config tells
    this script which event fired."""
    monkeypatch.setattr(hook, "config_dir", lambda: tmp_path)
    called = {}

    def fake_call(args):
        called["args"] = args
        return 0

    copilot_payload = {"sessionId": "abc", "timestamp": 1, "cwd": "/x", "prompt": "hi"}
    out = hook.main(copilot_payload, call_turnbreak=fake_call, argv=["--hint", "start"])
    assert out == {"ok": True}
    assert called["args"][0] == "start"

    called.clear()
    copilot_end_payload = {"sessionId": "abc", "timestamp": 2, "stopReason": "end_turn"}
    out2 = hook.main(copilot_end_payload, call_turnbreak=fake_call, argv=["--hint", "end"])
    assert out2 == {"ok": True}
    assert called["args"][0] == "stop"
