# Northstar Systems API Authentication

Category: Developer Support
Version: NS-API-2.4
Updated: 2026-08-19
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Authentication Model

Internal APIs use OAuth 2.0 bearer tokens issued by **Northstar Identity**. Services must send the token in the `Authorization` header.

```http
Authorization: Bearer <access-token>
```

## Token Requirements

- Audience must match the service identifier, for example `aud=support-api`.
- Tokens expire after 30 minutes.
- Service-to-service clients must use client credential profile **NS-SVC-CC-01**.
- User-facing tools must use authorization code with PKCE.

## Common Errors

- `API-AUTH-401`: token is missing, expired, or has the wrong audience.
- `API-AUTH-403`: token is valid but lacks the required role.
- `API-AUTH-429`: client exceeded the service rate limit.

## Resolution Steps

For `API-AUTH-401`, refresh the token and verify the audience. For `API-AUTH-403`, request the missing role through the access-request process. Never paste bearer tokens into chat, tickets, or screenshots.
