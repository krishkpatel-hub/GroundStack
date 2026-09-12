from pathlib import Path

from scripts.seed_demo import CORPUS_ID, corpus_paths, northstar_input


def test_northstar_corpus_contains_ten_markdown_documents() -> None:
    paths = corpus_paths(Path("docs/demo-corpus/northstar"))

    assert len(paths) == 10
    assert all(path.suffix == ".md" for path in paths)


def test_northstar_input_marks_sources_as_fictional_demo() -> None:
    payload = northstar_input(Path("docs/demo-corpus/northstar/04-db-104.md"))

    assert payload.display_name == "04-db-104.md"
    assert payload.source_metadata["corpus_id"] == CORPUS_ID
    assert payload.source_metadata["organization"] == "Northstar Systems"
    assert payload.source_metadata["fictional_demo"] is True
