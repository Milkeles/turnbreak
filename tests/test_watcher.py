from dataclasses import replace
from pathlib import Path

import pytest

from turnbreak.core import state
from turnbreak.core.watcher import make_is_cancelled, run, wait_for_threshold


class FakeClock:
    def __init__(self, start: float) -> None:
        self.current = start
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds


def test_wait_for_threshold_returns_true_once_reached():
    clock = FakeClock(100.0)
    reached = wait_for_threshold(100.0, 5.0, now=clock.now, sleep=clock.sleep, poll_interval=1.0)
    assert reached is True
    assert clock.current >= 105.0


def test_wait_for_threshold_does_not_overshoot_remaining_time():
    clock = FakeClock(100.0)
    wait_for_threshold(100.0, 2.5, now=clock.now, sleep=clock.sleep, poll_interval=1.0)
    assert clock.sleeps == [1.0, 1.0, 0.5]


def test_wait_for_threshold_stops_on_cancellation():
    clock = FakeClock(100.0)
    calls = []

    def is_cancelled() -> bool:
        calls.append(clock.current)
        return len(calls) >= 2

    reached = wait_for_threshold(
        100.0, 100.0, now=clock.now, sleep=clock.sleep, poll_interval=1.0, is_cancelled=is_cancelled
    )
    assert reached is False
    assert clock.sleeps == [1.0]


def test_wait_for_threshold_checks_cancellation_before_sleeping_when_already_cancelled():
    clock = FakeClock(100.0)
    reached = wait_for_threshold(
        100.0, 5.0, now=clock.now, sleep=clock.sleep, poll_interval=1.0, is_cancelled=lambda: True
    )
    assert reached is False
    assert clock.sleeps == []


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def test_make_is_cancelled_true_when_no_state(home):
    is_cancelled = make_is_cancelled("abc")
    assert is_cancelled() is True


def test_make_is_cancelled_false_while_turn_active(home):
    state.start_turn("abc", 100.0)
    is_cancelled = make_is_cancelled("abc")
    assert is_cancelled() is False


def test_make_is_cancelled_true_after_end_turn(home):
    state.start_turn("abc", 100.0)
    state.end_turn("abc")
    is_cancelled = make_is_cancelled("abc")
    assert is_cancelled() is True


def test_make_is_cancelled_true_for_mismatched_session(home):
    state.start_turn("abc", 100.0)
    is_cancelled = make_is_cancelled("some-other-session")
    assert is_cancelled() is True


def test_run_calls_on_fire_when_threshold_reached(home):
    config_path = home / ".config" / "turnbreak" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("threshold_seconds = 0\n")
    state.start_turn("abc", 0.0)

    fired = []
    run("abc", 0.0, on_fire=fired.append)

    assert fired == ["abc"]


def test_make_is_cancelled_true_when_held(home):
    started = state.start_turn("abc", 100.0)
    state.save_state(replace(started, hold_status="held"))
    is_cancelled = make_is_cancelled("abc")
    assert is_cancelled() is True


def test_run_does_not_call_on_fire_when_held(home):
    config_path = home / ".config" / "turnbreak" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("threshold_seconds = 0\n")
    started = state.start_turn("abc", 0.0)
    state.save_state(replace(started, hold_status="held"))

    fired = []
    run("abc", 0.0, on_fire=fired.append)

    assert fired == []


def test_run_does_not_call_on_fire_when_cancelled(home):
    config_path = home / ".config" / "turnbreak" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("threshold_seconds = 1000\n")
    state.start_turn("abc", 0.0)
    state.end_turn("abc")

    fired = []
    run("abc", 0.0, on_fire=fired.append)

    assert fired == []
