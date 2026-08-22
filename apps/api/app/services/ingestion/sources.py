import ipaddress
import mimetypes
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.settings import get_settings
from app.services.ingestion.types import IngestionInput, SourceValidationError

SUPPORTED_EXTENSIONS = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".html": "text/html",
    ".htm": "text/html",
    ".pdf": "application/pdf",
}
SUPPORTED_CONTENT_TYPES = {
    "text/markdown",
    "text/x-markdown",
    "text/plain",
    "text/html",
    "application/xhtml+xml",
    "application/pdf",
}


def guess_mime_type(name: str, supplied: str | None = None) -> str:
    if supplied:
        base = supplied.split(";")[0].strip().lower()
        if base in SUPPORTED_CONTENT_TYPES:
            return base
    extension = Path(name).suffix.lower()
    if extension in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[extension]
    guessed = mimetypes.guess_type(name)[0]
    if guessed in SUPPORTED_CONTENT_TYPES:
        return guessed
    raise SourceValidationError("Unsupported file type.", safe_details={"name": name})


def validate_file_size(size: int) -> None:
    max_size = get_settings().max_ingestion_file_size_bytes
    if size > max_size:
        raise SourceValidationError(
            "File exceeds maximum ingestion size.",
            safe_details={"max_size_bytes": max_size, "actual_size_bytes": size},
        )


def file_input_from_bytes(
    *, content: bytes, filename: str, content_type: str | None = None
) -> IngestionInput:
    validate_file_size(len(content))
    mime_type = guess_mime_type(filename, content_type)
    return IngestionInput(
        source_type="file",
        canonical_uri=f"file:{filename}",
        display_name=filename,
        mime_type=mime_type,
        content=content,
        source_metadata={"filename": filename, "size_bytes": len(content)},
    )


def file_input_from_path(path: Path) -> IngestionInput:
    if not path.exists() or not path.is_file():
        raise SourceValidationError("File does not exist.", safe_details={"path": str(path)})
    content = path.read_bytes()
    validate_file_size(len(content))
    mime_type = guess_mime_type(path.name)
    return IngestionInput(
        source_type="file",
        canonical_uri=f"file:{path.resolve()}",
        display_name=path.name,
        mime_type=mime_type,
        content=content,
        source_metadata={"path": str(path.resolve()), "size_bytes": len(content)},
    )


def _is_forbidden_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        [
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    )


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SourceValidationError("Only HTTP and HTTPS URLs are supported.")
    if parsed.username or parsed.password:
        raise SourceValidationError("URLs with embedded credentials are rejected.")
    if not parsed.hostname:
        raise SourceValidationError("URL must include a hostname.")
    hostname = parsed.hostname.lower()
    allowed = get_settings().url_ingestion_allowed_domains
    if hostname not in allowed:
        raise SourceValidationError(
            "URL hostname is not in the ingestion allowlist.",
            safe_details={"hostname": hostname},
        )
    try:
        infos = socket.getaddrinfo(
            hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
        )
    except socket.gaierror as exc:
        raise SourceValidationError("URL hostname could not be resolved.") from exc
    addresses = {info[4][0] for info in infos}
    if not addresses or any(_is_forbidden_ip(address) for address in addresses):
        raise SourceValidationError("URL resolves to a forbidden network address.")
    return url


async def url_input(url: str) -> IngestionInput:
    validated = validate_url(url)
    settings = get_settings()
    limits = httpx.Limits(max_connections=2, max_keepalive_connections=0)
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=httpx.Timeout(8.0, connect=4.0),
        limits=limits,
        headers={"User-Agent": "GroundStack-Ingestion/0.2"},
    ) as client:
        async with client.stream("GET", validated) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location", "")
                raise SourceValidationError(
                    "Redirects are not followed during URL ingestion.",
                    safe_details={"location": location[:200]},
                )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
            if content_type not in SUPPORTED_CONTENT_TYPES:
                raise SourceValidationError(
                    "URL returned an unsupported content type.",
                    safe_details={"content_type": content_type},
                )
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > settings.max_ingestion_file_size_bytes:
                    raise SourceValidationError("URL response exceeds maximum ingestion size.")
                chunks.append(chunk)
    parsed = urlparse(validated)
    display_name = Path(parsed.path).name or parsed.hostname or "submitted-url"
    return IngestionInput(
        source_type="url",
        canonical_uri=validated,
        display_name=display_name,
        mime_type=content_type,
        content=b"".join(chunks),
        source_metadata={"url": validated, "size_bytes": total},
    )
