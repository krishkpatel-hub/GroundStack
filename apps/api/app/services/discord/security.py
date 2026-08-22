from __future__ import annotations

import base64
import hmac
import time
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.core.settings import get_settings


class DiscordSecurityError(ValueError):
    pass


def verify_signature(*, body: bytes, timestamp: str, signature: str) -> None:
    settings = get_settings()
    if not settings.discord_public_key:
        raise DiscordSecurityError("Discord public key is not configured.")
    try:
        issued_at = int(timestamp)
    except ValueError as exc:
        raise DiscordSecurityError("Invalid Discord timestamp.") from exc
    if abs(int(time.time()) - issued_at) > settings.discord_signature_tolerance_seconds:
        raise DiscordSecurityError("Discord timestamp is outside the allowed window.")
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(settings.discord_public_key))
        key.verify(bytes.fromhex(signature), timestamp.encode("utf-8") + body)
    except Exception as exc:
        raise DiscordSecurityError("Invalid Discord signature.") from exc


def user_hmac(user_id: str) -> str:
    key = get_settings().discord_identity_hmac_key
    if not key:
        raise DiscordSecurityError("Discord identity HMAC key is not configured.")
    return hmac.new(key.encode("utf-8"), user_id.encode("utf-8"), sha256).hexdigest()


def _fernet() -> Fernet:
    key = get_settings().discord_interaction_token_encryption_key
    if not key:
        raise DiscordSecurityError("Discord token encryption key is not configured.")
    try:
        return Fernet(key.encode("ascii"))
    except Exception:
        digest = sha256(key.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_token(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise DiscordSecurityError("Stored Discord interaction token is invalid.") from exc
