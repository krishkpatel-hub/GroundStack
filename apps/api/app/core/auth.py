from __future__ import annotations

import time
from base64 import urlsafe_b64encode
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from typing import Annotated

import jwt
from authlib.common.security import generate_token
from fastapi import Depends, HTTPException, Request, Response, status
from jwt import PyJWKClient

from app.core.settings import Settings, get_settings


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]
    authenticated: bool
    anonymous: bool = False
    demo: bool = False

    @property
    def is_admin(self) -> bool:
        return get_settings().oidc_admin_role in self.roles or "admin" in self.roles


@lru_cache(maxsize=4)
def _jwk_client(issuer_url: str) -> PyJWKClient:
    jwks_url = issuer_url.rstrip("/") + "/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=300)


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if header:
        scheme, _, token = header.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token
    cookie_token = request.cookies.get(get_settings().session_cookie_name)
    return cookie_token or None


def pkce_challenge(verifier: str) -> str:
    digest = sha256(verifier.encode("ascii")).digest()
    return urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def set_oidc_flow_cookies(response: Response, *, state: str, nonce: str, verifier: str) -> None:
    settings = get_settings()
    for name, value in {
        "groundstack_oidc_state": state,
        "groundstack_oidc_nonce": nonce,
        "groundstack_oidc_verifier": verifier,
    }.items():
        response.set_cookie(
            name,
            value,
            httponly=True,
            secure=settings.session_cookie_secure,
            samesite=settings.session_cookie_samesite,
            max_age=600,
        )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    for name in [
        settings.session_cookie_name,
        "groundstack_oidc_state",
        "groundstack_oidc_nonce",
        "groundstack_oidc_verifier",
    ]:
        response.delete_cookie(name)


def new_oidc_flow() -> tuple[str, str, str]:
    return generate_token(32), generate_token(32), generate_token(64)


def _roles(payload: dict[str, object], settings: Settings) -> frozenset[str]:
    value = payload.get(settings.oidc_role_claim, [])
    if isinstance(value, str):
        return frozenset([value])
    if isinstance(value, list):
        return frozenset(str(item) for item in value)
    return frozenset()


async def validate_access_token(token: str, settings: Settings | None = None) -> Principal:
    settings = settings or get_settings()
    if not settings.oidc_issuer_url or not settings.oidc_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC is not configured."
        )
    unverified_header = jwt.get_unverified_header(token)
    alg = unverified_header.get("alg")
    if not alg or alg == "none" or alg not in settings.oidc_allowed_algorithms:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported token algorithm."
        )
    signing_key = _jwk_client(settings.oidc_issuer_url).get_signing_key_from_jwt(token)
    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=settings.oidc_allowed_algorithms,
            audience=settings.oidc_audience or settings.oidc_client_id,
            issuer=settings.oidc_issuer_url.rstrip("/"),
            leeway=30,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token."
        ) from exc
    subject = str(payload.get("sub", "")).strip()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token subject is missing."
        )
    return Principal(subject=subject, roles=_roles(payload, settings), authenticated=True)


async def validate_id_token(
    token: str, *, expected_nonce: str, settings: Settings | None = None
) -> dict[str, object]:
    settings = settings or get_settings()
    if not settings.oidc_issuer_url or not settings.oidc_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="OIDC is not configured."
        )
    unverified_header = jwt.get_unverified_header(token)
    alg = unverified_header.get("alg")
    if not alg or alg == "none" or alg not in settings.oidc_allowed_algorithms:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported token algorithm."
        )
    signing_key = _jwk_client(settings.oidc_issuer_url).get_signing_key_from_jwt(token)
    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=settings.oidc_allowed_algorithms,
            audience=settings.oidc_client_id,
            issuer=settings.oidc_issuer_url.rstrip("/"),
            leeway=30,
            options={"require": ["exp", "iat", "sub", "nonce"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token."
        ) from exc
    if not expected_nonce or payload.get("nonce") != expected_nonce:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OIDC nonce.")
    return dict(payload)


def _development_principal(request: Request, settings: Settings) -> Principal | None:
    if settings.app_env != "development" or not settings.dev_auth_bypass_enabled:
        return None
    subject = request.headers.get("x-groundstack-dev-user", "dev-user")
    role = request.headers.get("x-groundstack-dev-role", settings.oidc_admin_role)
    return Principal(subject=f"dev:{subject}", roles=frozenset([role]), authenticated=True)


def _anonymous_demo_principal(request: Request, settings: Settings) -> Principal | None:
    if settings.app_env != "demo" or not settings.allow_anonymous_demo:
        return None
    demo_id = request.headers.get("x-groundstack-demo-id")
    if not demo_id and request.client:
        demo_id = f"ip:{request.client.host}"
    if not demo_id:
        demo_id = f"demo:{int(time.time() // 3600)}"
    return Principal(
        subject=f"anon:{demo_id[:80]}",
        roles=frozenset(["demo_anonymous"]),
        authenticated=False,
        anonymous=True,
        demo=True,
    )


async def optional_principal(request: Request) -> Principal | None:
    settings = get_settings()
    dev = _development_principal(request, settings)
    if dev:
        return dev
    token = _bearer_token(request)
    if token:
        return await validate_access_token(token, settings)
    return _anonymous_demo_principal(request, settings)


OptionalPrincipal = Annotated[Principal | None, Depends(optional_principal)]


async def require_user(principal: OptionalPrincipal) -> Principal:
    if principal is None or principal.anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )
    return principal


async def require_chat_actor(principal: OptionalPrincipal) -> Principal:
    settings = get_settings()
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )
    if principal.anonymous and not (settings.app_env == "demo" and settings.allow_anonymous_demo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )
    return principal


UserPrincipal = Annotated[Principal, Depends(require_user)]
ChatPrincipal = Annotated[Principal, Depends(require_chat_actor)]


async def require_admin(principal: UserPrincipal) -> Principal:
    if not principal.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return principal


AdminPrincipal = Annotated[Principal, Depends(require_admin)]
