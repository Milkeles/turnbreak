from turnbreak.core.items import Item, append_history
from turnbreak.sources.finder import FinderContext, build_context


def make_item(title="Example", locator="https://example.com/a", word_count=460, source="curated"):
    return Item(title=title, locator=locator, word_count=word_count, source=source)


def test_build_context_reads_interests_and_splits_history_by_outcome(tmp_path):
    interests_file = tmp_path / "interests.md"
    interests_file.write_text("Rust, distributed systems\n")
    history_file = tmp_path / "history.jsonl"
    append_history(make_item("Read one", locator="https://a"), "match", history_file)
    append_history(make_item("Skip one", locator="https://b"), "miss", history_file)

    context = build_context(interests_file, history_file)

    assert context.interests == "Rust, distributed systems\n"
    assert [item.locator for item in context.read_items] == ["https://a"]
    assert [item.locator for item in context.skipped_items] == ["https://b"]


def test_build_context_with_no_files_returns_empty_context(tmp_path):
    context = build_context(tmp_path / "interests.md", tmp_path / "history.jsonl")
    assert context == FinderContext(interests="", read_items=[], skipped_items=[])


def test_a_finder_implementation_satisfies_the_protocol():
    class StubFinder:
        def find(self, context: FinderContext) -> list[Item]:
            return [make_item()]

    finder = StubFinder()
    context = FinderContext(interests="", read_items=[], skipped_items=[])
    assert finder.find(context) == [make_item()]
