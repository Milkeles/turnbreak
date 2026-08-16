import json
from pathlib import Path
import importlib.util


# Load the hook script directly by path to avoid relying on top-level
# 'scripts' package being importable in every test environment.
_hook_path = Path(__file__).resolve().parent.parent / "scripts" / "turnbreak-hook.py"
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
    monkeypatch.setattr(hook, 'config_dir', lambda: tmp_path)
    called = {}

    def fake_call(args):
        called['args'] = args
        return 0

    payload = {"UserPromptSubmit": {"prompt": "hi"}}
    out = hook.main(payload, call_turnbreak=fake_call)
    assert out == {"ok": True}
    assert 'args' in called and called['args'][0] == 'start'
    # session file created
    assert (tmp_path / 'hook_last_session').exists()

    # Now simulate end event using recorded session id
    called.clear()
    out2 = hook.main({"Stop": {}}, call_turnbreak=fake_call)
    assert out2 == {"ok": True}
    assert 'args' in called and called['args'][0] == 'stop'
