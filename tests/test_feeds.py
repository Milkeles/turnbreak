from turnbreak.core.feeds import load_feeds


def test_load_feeds_missing_file_returns_empty_list(tmp_path):
    assert load_feeds(tmp_path / "feeds.txt") == []


def test_load_feeds_reads_one_url_per_line(tmp_path):
    path = tmp_path / "feeds.txt"
    path.write_text("https://a.example/feed.xml\nhttps://b.example/feed.xml\n")
    assert load_feeds(path) == ["https://a.example/feed.xml", "https://b.example/feed.xml"]


def test_load_feeds_skips_blank_lines(tmp_path):
    path = tmp_path / "feeds.txt"
    path.write_text("https://a.example/feed.xml\n\n\nhttps://b.example/feed.xml\n")
    assert load_feeds(path) == ["https://a.example/feed.xml", "https://b.example/feed.xml"]
