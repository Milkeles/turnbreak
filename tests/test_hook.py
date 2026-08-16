import json
from pathlib import Path

import scripts.turnbreak_hook as hook


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
