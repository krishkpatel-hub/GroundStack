# Failure Recovery Plan

Failure scenarios are defined in `scripts/failure_test.py`. They are safe manifests by default and
must run only against local or explicitly approved test infrastructure.

## Scenarios

- PostgreSQL unavailable or slow.
- Connection pool exhaustion.
- Redis unavailable or slow.
- Generation provider timeout, HTTP 429, HTTP 500, connection failure, malformed response, or stream
  interruption.
- Worker termination and restart.
- Queue backlog and expiration.
- Invalid embedding dimensions.
- Empty corpus and corrupted citation metadata.
- Expired or duplicate Discord interactions.
- Frontend disconnects and application restarts during traffic.

## Required Evidence

Each scenario report must record:

- Detection time.
- Recovery time.
- Readiness behavior.
- Accepted work completed or visible failure state.
- No silent data corruption.
- Dependency restoration steps.
- Post-test integrity-check results.

## Current Result

No destructive or network fault was injected in this milestone run. The failure scenario manifest and
validation commands were added so future local runs can produce evidence without touching public
third-party services.
