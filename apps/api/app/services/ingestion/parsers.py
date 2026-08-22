import re
from abc import ABC, abstractmethod
from importlib.metadata import version
from io import BytesIO

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from pypdf import PdfReader

from app.services.ingestion.normalization import normalize_text
from app.services.ingestion.types import ExtractedDocument, ExtractionError, ParsedBlock


class DocumentParser(ABC):
    parser_name: str

    @abstractmethod
    def parse(self, content: bytes, *, display_name: str, mime_type: str) -> ExtractedDocument:
        raise NotImplementedError


def _decode(content: bytes) -> str:
    return content.decode("utf-8-sig", errors="replace")


def _package_version(package: str) -> str:
    try:
        return version(package)
    except Exception:
        return "unknown"


def markdown_blocks(text: str) -> list[ParsedBlock]:
    md = MarkdownIt("commonmark")
    tokens = md.parse(text)
    headings: list[tuple[int, str]] = []
    blocks: list[ParsedBlock] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "heading_open":
            level = int(token.tag[1])
            title = tokens[i + 1].content.strip() if i + 1 < len(tokens) else ""
            headings = [(lvl, value) for lvl, value in headings if lvl < level]
            headings.append((level, title))
            blocks.append(
                ParsedBlock(
                    text=f"{'#' * level} {title}",
                    heading_path=tuple(v for _, v in headings),
                    kind="heading",
                )
            )
            i += 3
            continue
        if token.type in {"paragraph_open", "fence", "code_block"}:
            if token.type in {"fence", "code_block"}:
                info = token.info.strip() if hasattr(token, "info") else ""
                body = token.content.rstrip()
                text_block = f"```{info}\n{body}\n```"
                kind = "code"
            else:
                inline = next(
                    (
                        tokens[j]
                        for j in range(i + 1, min(i + 4, len(tokens)))
                        if tokens[j].type == "inline"
                    ),
                    None,
                )
                text_block = inline.content.strip() if inline else token.content.strip()
                kind = "paragraph"
            if text_block:
                blocks.append(
                    ParsedBlock(
                        text=text_block, heading_path=tuple(v for _, v in headings), kind=kind
                    )
                )
        i += 1
    return blocks or [ParsedBlock(text=text)]


class MarkdownParser(DocumentParser):
    parser_name = "markdown-it-py"

    def parse(self, content: bytes, *, display_name: str, mime_type: str) -> ExtractedDocument:
        text = normalize_text(_decode(content))
        if not text:
            raise ExtractionError("Markdown document has no extractable text.")
        title = next(
            (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")),
            display_name,
        )
        return ExtractedDocument(
            title=title,
            mime_type=mime_type,
            text=text,
            metadata={
                "parser": self.parser_name,
                "parser_version": _package_version("markdown-it-py"),
                "blocks": [block.__dict__ for block in markdown_blocks(text)],
            },
        )


class PlainTextParser(DocumentParser):
    parser_name = "plain-text"

    def parse(self, content: bytes, *, display_name: str, mime_type: str) -> ExtractedDocument:
        text = normalize_text(_decode(content))
        if not text:
            raise ExtractionError("Text document has no usable content.")
        return ExtractedDocument(
            title=display_name,
            mime_type=mime_type,
            text=text,
            metadata={"parser": self.parser_name, "parser_version": "builtin"},
        )


class HtmlParser(DocumentParser):
    parser_name = "beautifulsoup4"

    def parse(self, content: bytes, *, display_name: str, mime_type: str) -> ExtractedDocument:
        soup = BeautifulSoup(_decode(content), "html.parser")
        for selector in ["script", "style", "nav", "footer", "header", "aside", "noscript"]:
            for element in soup.select(selector):
                element.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else display_name
        container = soup.find("main") or soup.find("article") or soup.body or soup
        lines: list[str] = []
        for element in container.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "pre", "code", "td", "th"]
        ):
            text = element.get_text(" ", strip=False if element.name in {"pre", "code"} else True)
            text = text.strip("\n")
            if not text:
                continue
            if element.name in {"h1", "h2", "h3", "h4"}:
                level = int(element.name[1])
                lines.append(f"{'#' * level} {text.strip()}")
            elif element.name == "li":
                lines.append(f"- {text.strip()}")
            elif element.name == "pre":
                lines.append(f"```\n{text.rstrip()}\n```")
            else:
                lines.append(text.strip())
        text = normalize_text("\n\n".join(lines))
        if not text:
            raise ExtractionError("HTML document has no meaningful content.")
        return ExtractedDocument(
            title=title,
            mime_type=mime_type,
            text=text,
            metadata={
                "parser": self.parser_name,
                "parser_version": _package_version("beautifulsoup4"),
            },
        )


class PdfParser(DocumentParser):
    parser_name = "pypdf"

    def parse(self, content: bytes, *, display_name: str, mime_type: str) -> ExtractedDocument:
        try:
            reader = PdfReader(BytesIO(content))
            pages = [
                {"page": index + 1, "text": page.extract_text() or ""}
                for index, page in enumerate(reader.pages)
            ]
        except Exception as exc:
            raise ExtractionError("PDF could not be parsed.") from exc
        page_text = [
            f"[Page {page['page']}]\n{page['text']}" for page in pages if str(page["text"]).strip()
        ]
        text = normalize_text("\n\n".join(page_text))
        if len(re.sub(r"\s+", "", text)) < 20:
            raise ExtractionError("PDF appears to be scanned or has no extractable text.")
        return ExtractedDocument(
            title=display_name,
            mime_type=mime_type,
            text=text,
            metadata={
                "parser": self.parser_name,
                "parser_version": _package_version("pypdf"),
                "page_count": len(reader.pages),
                "pages_with_text": len(page_text),
            },
        )


def parser_for(mime_type: str, display_name: str) -> DocumentParser:
    name = display_name.lower()
    if mime_type in {"text/markdown", "text/x-markdown"} or name.endswith((".md", ".markdown")):
        return MarkdownParser()
    if mime_type in {"text/plain"} or name.endswith(".txt"):
        return PlainTextParser()
    if mime_type in {"text/html", "application/xhtml+xml"} or name.endswith((".html", ".htm")):
        return HtmlParser()
    if mime_type == "application/pdf" or name.endswith(".pdf"):
        return PdfParser()
    raise ExtractionError("Unsupported document type.", safe_details={"mime_type": mime_type})
