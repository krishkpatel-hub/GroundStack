from __future__ import annotations

from urllib.parse import urlencode

import httpx
from authlib.common.security import generate_token
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.auth import (
    clear_auth_cookies,
    new_oidc_flow,
    pkce_challenge,
    set_oidc_flow_cookies,
    validate_access_token,
    validate_id_token,
)
from app.core.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


async def _discovery() -> dict[str, object]:
    settings = get_settings()
    if not settings.oidc_issuer_url:
        raise HTTPException(status_code=503, detail="OIDC issuer is not configured.")
    url = settings.oidc_issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@router.get("/login")
async def login() -> RedirectResponse:
    settings = get_settings()
    if settings.app_env == "development" and settings.dev_auth_bypass_enabled:
        return RedirectResponse(url="/api/v1/auth/me")
    if not settings.oidc_client_id:
        raise HTTPException(status_code=503, detail="OIDC client is not configured.")
    discovery = await _discovery()
    authorization_endpoint = str(discovery["authorization_endpoint"])
    state, nonce, verifier = new_oidc_flow()
    redirect_uri = settings.public_api_base_url.rstrip("/") + "/api/v1/auth/callback"
    params = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": redirect_uri,
        "scope": settings.oidc_scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": pkce_challenge(verifier),
        "code_challenge_method": "S256",
    }
    if settings.oidc_audience:
        params["audience"] = settings.oidc_audience
    response = RedirectResponse(url=authorization_endpoint + "?" + urlencode(params))
    set_oidc_flow_cookies(response, state=state, nonce=nonce, verifier=verifier)
    return response


@router.get("/callback")
async def callback(request: Request) -> RedirectResponse:
    settings = get_settings()
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    if not code or not state or state != request.cookies.get("groundstack_oidc_state"):
        raise HTTPException(status_code=400, detail="Invalid OIDC callback state.")
    verifier = request.cookies.get("groundstack_oidc_verifier")
    if not verifier:
        raise HTTPException(status_code=400, detail="Missing OIDC PKCE verifier.")
    discovery = await _discovery()
    redirect_uri = settings.public_api_base_url.rstrip("/") + "/api/v1/auth/callback"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.oidc_client_id,
        "code_verifier": verifier,
    }
    if settings.oidc_client_secret:
        payload["client_secret"] = settings.oidc_client_secret
    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(str(discovery["token_endpoint"]), data=payload)
        token_response.raise_for_status()
        tokens = token_response.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="OIDC provider did not return an access token.")
    id_token = tokens.get("id_token")
    nonce = request.cookies.get("groundstack_oidc_nonce")
    if not id_token:
        raise HTTPException(status_code=502, detail="OIDC provider did not return an ID token.")
    await validate_id_token(str(id_token), expected_nonce=nonce or "", settings=settings)
    await validate_access_token(str(access_token), settings)
    response = RedirectResponse(url="/")
    response.set_cookie(
        settings.session_cookie_name,
        str(access_token),
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_lifetime_seconds,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        generate_token(32),
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_lifetime_seconds,
    )
    return response


@router.post("/logout")
async def logout() -> JSONResponse:
    response = JSONResponse({"status": "logged_out"})
    clear_auth_cookies(response)
    return response


@router.get("/me")
async def me(request: Request) -> dict[str, object]:
    from app.core.auth import optional_principal

    principal = await optional_principal(request)
    if principal is None:
        return {"authenticated": False, "roles": [], "admin": False}
    return {
        "authenticated": principal.authenticated,
        "anonymous": principal.anonymous,
        "subject": principal.subject,
        "roles": sorted(principal.roles),
        "admin": principal.is_admin,
    }
