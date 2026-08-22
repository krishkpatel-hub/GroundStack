# ADR 0001: Authentication And Deployment Topology

## Status

Accepted for Milestone 8.

## Decision

GroundStack uses provider-neutral OIDC with Authorization Code + PKCE for browser sign-in and
backend JWKS validation for bearer/session access tokens. The app avoids a custom password system.

Deployment supports a single-host demo Compose topology and a managed-production topology using the
same containers with managed PostgreSQL, Redis, TLS/load balancing, and inference services.

## Consequences

Operators must choose and configure an OIDC provider before production. Anonymous demo access is
explicitly gated by `APP_ENV=demo` and `ALLOW_ANONYMOUS_DEMO=true`.
