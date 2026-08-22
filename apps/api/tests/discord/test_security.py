import json
import time
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.discord.security import (
    DiscordSecurityError,
    decrypt_token,
    encrypt_token,
    verify_signature,
)


def _keys() -> tuple[Ed25519PrivateKey, str]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private, public.hex()


def _settings(public_key: str) -> SimpleNamespace:
    return SimpleNamespace(
        discord_public_key=public_key,
        discord_signature_tolerance_seconds=300,
        discord_interaction_token_encryption_key="test-token-key",
    )


def _signed_headers(private: Ed25519PrivateKey, body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    signature = private.sign(timestamp.encode("utf-8") + body).hex()
    return {
        "x-signature-timestamp": timestamp,
        "x-signature-ed25519": signature,
        "content-type": "application/json",
    }


def test_signature_verification_accepts_valid_payload(monkeypatch) -> None:
    private, public_key = _keys()
    body = b'{"type":1}'
    headers = _signed_headers(private, body)
    monkeypatch.setattr("app.services.discord.security.get_settings", lambda: _settings(public_key))

    verify_signature(
        body=body,
        timestamp=headers["x-signature-timestamp"],
        signature=headers["x-signature-ed25519"],
    )


def test_signature_verification_rejects_old_timestamp(monkeypatch) -> None:
    private, public_key = _keys()
    body = b'{"type":1}'
    timestamp = str(int(time.time()) - 1000)
    signature = private.sign(timestamp.encode("utf-8") + body).hex()
    monkeypatch.setattr("app.services.discord.security.get_settings", lambda: _settings(public_key))

    with pytest.raises(DiscordSecurityError):
        verify_signature(body=body, timestamp=timestamp, signature=signature)


def test_token_encryption_round_trips(monkeypatch) -> None:
    _, public_key = _keys()
    monkeypatch.setattr("app.services.discord.security.get_settings", lambda: _settings(public_key))

    encrypted = encrypt_token("interaction-token")

    assert encrypted != "interaction-token"
    assert decrypt_token(encrypted) == "interaction-token"


@pytest.mark.asyncio
async def test_discord_ping_response(monkeypatch) -> None:
    private, public_key = _keys()
    body = json.dumps({"type": 1}).encode("utf-8")
    headers = _signed_headers(private, body)
    monkeypatch.setattr("app.services.discord.security.get_settings", lambda: _settings(public_key))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/integrations/discord/interactions", content=body, headers=headers
        )

    assert response.status_code == 200
    assert response.json() == {"type": 1}
