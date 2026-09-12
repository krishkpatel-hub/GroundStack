# Northstar Systems Deployment Rollback Procedure

Category: Release Operations
Version: NS-REL-4.2
Updated: 2026-08-20
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Before Rolling Back

Before rolling back a failed deployment, complete these checks:

1. Confirm the incident commander or release owner approves rollback.
2. Capture the failed release version, commit SHA, and deployment ID.
3. Check whether the release included database migrations.
4. Verify the previous release artifact is still available.
5. Notify the support channel `#northstar-release-watch`.

## Rollback Command

Use the deployment controller:

```bash
northstarctl deploy rollback --service <service> --to-version <version> --ticket <incident-ticket>
```

## Database Caution

If the failed release included a forward-only migration, do not rollback the application until Database Support confirms compatibility. Use feature flag disablement first when available.

## Verification

After rollback, confirm `/health/ready` is healthy, error rate returns to baseline, and customer-impacting alerts close.
