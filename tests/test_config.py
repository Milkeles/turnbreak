from turnbreak.core.config import Config, load_config


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
