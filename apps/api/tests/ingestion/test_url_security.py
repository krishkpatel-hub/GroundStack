import socket

import pytest

from app.core.settings import get_settings
from app.services.ingestion.sources import validate_url
from app.services.ingestion.types import SourceValidationError


def test_url_rejects_credentials(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "url_ingestion_allowed_domains", ["docs.example.com"])
    with pytest.raises(SourceValidationError):
        validate_url("https://user:pass@docs.example.com/page")


def test_url_rejects_unallowed_domain(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "url_ingestion_allowed_domains", ["docs.example.com"])
    with pytest.raises(SourceValidationError):
        validate_url("https://other.example.com/page")


def test_url_rejects_private_resolved_address(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "url_ingestion_allowed_domains", ["docs.example.com"])
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(SourceValidationError):
        validate_url("https://docs.example.com/page")


def test_url_accepts_public_allowlisted_host(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "url_ingestion_allowed_domains", ["docs.example.com"])
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    assert validate_url("https://docs.example.com/page") == "https://docs.example.com/page"
