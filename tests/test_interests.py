from turnbreak.core.interests import load_interests


def test_load_interests_missing_file_returns_empty_string(tmp_path):
    assert load_interests(tmp_path / "interests.md") == ""


def test_load_interests_reads_file_contents(tmp_path):
    path = tmp_path / "interests.md"
    path.write_text("Rust, distributed systems, climbing\n")
    assert load_interests(path) == "Rust, distributed systems, climbing\n"
