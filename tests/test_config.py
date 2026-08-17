import pathlib

import pytest

from turnbreak.core.config import Config, atomic_write_text, load_config, save_config


def test_atomic_write_text_overwrites_existing_content(tmp_path):
    path = tmp_path / "f.txt"
    path.write_text("old")
    atomic_write_text(path, "new")
    assert path.read_text() == "new"
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_text_cleans_up_temp_file_on_failure(tmp_path, monkeypatch):
    path = tmp_path / "f.txt"

    def boom(self, data):
        raise OSError("No space left on device")

    monkeypatch.setattr(pathlib.Path, "write_text", boom)
    with pytest.raises(OSError):
        atomic_write_text(path, "new")
    monkeypatch.undo()
    assert list(tmp_path.iterdir()) == []


def test_load_config_missing_file_returns_defaults(tmp_path):
    path = tmp_path / "config.toml"
    assert load_config(path) == Config()


def test_load_config_overrides_from_file(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        "port = 8000\n"
        "threshold_seconds = 30\n"
        "words_per_minute = 200\n"
        "target_read_minutes = [1, 3]\n"
        'mode = "folder"\n'
    )
    cfg = load_config(path)
    assert cfg.port == 8000
    assert cfg.threshold_seconds == 30
    assert cfg.words_per_minute == 200
    assert cfg.target_read_minutes == (1, 3)
    assert cfg.mode == "folder"


def test_load_config_partial_file_keeps_remaining_defaults(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("port = 9000\n")
    cfg = load_config(path)
    assert cfg.port == 9000
    assert cfg.threshold_seconds == Config().threshold_seconds
    assert cfg.mode == Config().mode


def test_save_and_load_config_round_trips(tmp_path):
    path = tmp_path / "config.toml"
    original = Config(mode="folder", folder_path="/home/user/reading")
    save_config(original, path)
    assert load_config(path) == original


def test_save_config_escapes_special_characters_in_folder_path(tmp_path):
    path = tmp_path / "config.toml"
    original = Config(mode="folder", folder_path='C:\\docs\\"quoted"')
    save_config(original, path)
    assert load_config(path).folder_path == 'C:\\docs\\"quoted"'


def test_save_and_load_config_round_trips_agent_finder_accepted(tmp_path):
    path = tmp_path / "config.toml"
    original = Config(agent_finder_accepted=True)
    save_config(original, path)
    assert load_config(path).agent_finder_accepted is True


def test_load_config_defaults_finder_to_agent(tmp_path):
    assert Config().finder == "agent"


def test_save_and_load_config_round_trips_finder(tmp_path):
    path = tmp_path / "config.toml"
    original = Config(finder="rss")
    save_config(original, path)
    assert load_config(path).finder == "rss"


def test_load_config_torn_file_returns_defaults(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('port = 8000\nmode = "fol')  # cut off mid-write
    assert load_config(path) == Config()


def test_save_config_leaves_no_temp_file(tmp_path):
    path = tmp_path / "config.toml"
    save_config(Config(), path)
    assert list(tmp_path.iterdir()) == [path]
