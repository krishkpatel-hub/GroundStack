import pytest

from app.services.ai.embeddings import SentenceTransformerEmbeddingProvider
from app.services.ai.types import EmbeddingRequest
from app.services.ingestion.checksums import sha256_text
from app.services.ingestion.chunking import ChunkingConfig, StructureAwareChunker
from app.services.ingestion.normalization import normalize_text
from app.services.ingestion.parsers import HtmlParser, MarkdownParser, PlainTextParser
from app.services.ingestion.types import EmbeddingError


def test_markdown_parser_preserves_headings_and_code() -> None:
    parsed = MarkdownParser().parse(
        b"# Install\n\n## Step One\n\nRun `make dev`.\n\n```bash\nmake migrate\n```",
        display_name="setup.md",
        mime_type="text/markdown",
    )
    assert parsed.title == "Install"
    assert "```bash" in parsed.text
    assert parsed.metadata["parser"] == "markdown-it-py"


def test_html_parser_removes_navigation() -> None:
    parsed = HtmlParser().parse(
        b"<html><nav>Menu</nav><main><h1>Docs</h1><p>Useful content.</p></main></html>",
        display_name="docs.html",
        mime_type="text/html",
    )
    assert "Useful content" in parsed.text
    assert "Menu" not in parsed.text


def test_plain_text_parser_and_normalization() -> None:
    parsed = PlainTextParser().parse(
        b"Hello\r\n\r\n   world\t\tagain", display_name="a.txt", mime_type="text/plain"
    )
    assert parsed.text == "Hello\n\nworld again"
    assert normalize_text("a\n\n\nb") == "a\n\nb"


def test_chunker_nested_headings_overlap_and_stable_hashes() -> None:
    text = "# A\n\n## B\n\n" + " ".join(f"word{i}" for i in range(80)) + "\n\n## C\n\nsmall"
    chunker = StructureAwareChunker(ChunkingConfig(target_tokens=30, overlap_tokens=5))
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert chunks[0].position == 0
    assert chunks == chunker.chunk(text)
    assert all(chunk.checksum == sha256_text(chunk.content) for chunk in chunks)
    assert any("B" in chunk.heading_path for chunk in chunks)


def test_chunker_keeps_code_block_together() -> None:
    text = "# Code\n\n```python\n" + "\n".join(f"print({i})" for i in range(20)) + "\n```\n\nAfter."
    chunks = StructureAwareChunker(ChunkingConfig(target_tokens=15, overlap_tokens=2)).chunk(text)
    assert any("```python" in chunk.content and "print(19)" in chunk.content for chunk in chunks)


def test_chunker_unicode_and_small_document() -> None:
    chunks = StructureAwareChunker(ChunkingConfig(target_tokens=350, overlap_tokens=60)).chunk(
        "Café setup ✅"
    )
    assert len(chunks) == 1
    assert chunks[0].content == "Café setup ✅"


def test_chunker_trailing_merge_does_not_duplicate_overlap() -> None:
    text = "# A\n\n" + " ".join(f"word{i}" for i in range(35)) + "\n\nFinal note."
    chunks = StructureAwareChunker(ChunkingConfig(target_tokens=30, overlap_tokens=5)).chunk(text)
    combined = "\n\n".join(chunk.content for chunk in chunks)
    assert combined.count("word30") == 1


class WrongDimensionProvider(SentenceTransformerEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__(model_name="test", dimension=384, batch_size=1, device="cpu")

    def _embed_sync(self, inputs: list[str], mode: str):
        raise EmbeddingError(
            "Embedding dimension mismatch.", safe_details={"expected": 384, "actual": 2}
        )


async def test_embedding_dimension_validation_failure() -> None:
    with pytest.raises(EmbeddingError):
        await WrongDimensionProvider().embed(EmbeddingRequest(inputs=["hello"]))
