import re
from dataclasses import dataclass

from app.services.ingestion.checksums import sha256_text
from app.services.ingestion.parsers import markdown_blocks
from app.services.ingestion.types import DocumentChunkPayload, ParsedBlock

TOKEN_RE = re.compile(r"\S+")


def estimate_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(text))


def _words(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


@dataclass(frozen=True)
class ChunkingConfig:
    target_tokens: int = 350
    overlap_tokens: int = 60


class StructureAwareChunker:
    def __init__(self, config: ChunkingConfig) -> None:
        self.config = config

    def chunk(self, text: str) -> list[DocumentChunkPayload]:
        blocks = markdown_blocks(text)
        chunks: list[tuple[list[str], str, dict[str, object]]] = []
        current: list[ParsedBlock] = []
        current_tokens = 0

        for block in blocks:
            block_tokens = estimate_tokens(block.text)
            if (
                block.kind == "code"
                and current
                and current_tokens + block_tokens > self.config.target_tokens
            ):
                chunks.append(self._render(current))
                current = self._overlap_blocks(current)
                current_tokens = estimate_tokens("\n\n".join(item.text for item in current))
            if block_tokens > self.config.target_tokens * 1.4 and block.kind != "code":
                if current:
                    chunks.append(self._render(current))
                    current = []
                    current_tokens = 0
                chunks.extend(self._split_long_block(block))
                continue
            if current and current_tokens + block_tokens > self.config.target_tokens:
                chunks.append(self._render(current))
                current = self._overlap_blocks(current)
                current_tokens = estimate_tokens("\n\n".join(item.text for item in current))
            current.append(block)
            current_tokens += block_tokens

        if current:
            rendered = self._render(current)
            if chunks and estimate_tokens(rendered[1]) < max(80, self.config.target_tokens // 4):
                previous_path, previous_text, previous_meta = chunks.pop()
                merged = self._merge_without_duplicate_blocks(previous_text, rendered[1])
                chunks.append((previous_path, merged, {**previous_meta, "merged_trailing": True}))
            else:
                chunks.append(rendered)

        return [
            DocumentChunkPayload(
                position=index,
                heading_path=path,
                content=content,
                token_count=estimate_tokens(content),
                checksum=sha256_text(content),
                metadata=metadata,
            )
            for index, (path, content, metadata) in enumerate(chunks)
            if content.strip()
        ]

    def _render(self, blocks: list[ParsedBlock]) -> tuple[list[str], str, dict[str, object]]:
        path = list(blocks[-1].heading_path or blocks[0].heading_path)
        return (
            path,
            "\n\n".join(block.text for block in blocks).strip(),
            {"block_count": len(blocks)},
        )

    def _merge_without_duplicate_blocks(self, previous_text: str, trailing_text: str) -> str:
        previous_blocks = [block.strip() for block in previous_text.split("\n\n") if block.strip()]
        seen = set(previous_blocks)
        additions = [
            block.strip()
            for block in trailing_text.split("\n\n")
            if block.strip() and block.strip() not in seen
        ]
        return "\n\n".join([*previous_blocks, *additions]).strip()

    def _overlap_blocks(self, blocks: list[ParsedBlock]) -> list[ParsedBlock]:
        if self.config.overlap_tokens <= 0:
            return []
        kept: list[ParsedBlock] = []
        total = 0
        for block in reversed(blocks):
            total += estimate_tokens(block.text)
            kept.insert(0, block)
            if total >= self.config.overlap_tokens:
                break
        return kept

    def _split_long_block(
        self, block: ParsedBlock
    ) -> list[tuple[list[str], str, dict[str, object]]]:
        words = _words(block.text)
        step = max(1, self.config.target_tokens - self.config.overlap_tokens)
        parts: list[tuple[list[str], str, dict[str, object]]] = []
        for start in range(0, len(words), step):
            part = " ".join(words[start : start + self.config.target_tokens]).strip()
            if part:
                parts.append((list(block.heading_path), part, {"split_from": block.kind}))
        return parts
