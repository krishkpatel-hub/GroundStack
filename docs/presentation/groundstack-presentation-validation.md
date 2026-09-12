# GroundStack Presentation Validation Document

Document type: Temporary presentation validation file
Version: 1.0
Updated: September 11, 2026

This original document exists only to validate GroundStack during a local presentation. It contains no private, customer, municipal, or production information. It is not loaded automatically.

## Error GS-DEMO-217

`GS-DEMO-217` means the validation worker started but could not confirm that its active configuration revision matches the revision approved by the application.

The most common cause is a stale local configuration cache after a configuration file has changed. The worker remains unavailable until the active revision is refreshed and verified.

## Resolution

Resolve `GS-DEMO-217` in this order:

1. Open the worker status page and record the active configuration revision.
2. Compare it with the revision marked Approved in the configuration panel.
3. Select **Refresh configuration**. Do not edit the approved revision during this step.
4. Restart only the validation worker after the refresh reports complete.
5. Return to the worker status page and confirm `validation_status=ready`.
6. Run the built-in validation check once. The check must finish with `revision_match=true` before the incident is closed.

If the revisions still differ after one refresh, stop retrying and ask the application owner to inspect the configuration publication log. Do not bypass the revision check.

## Verification evidence

A successful recovery has both of these values:

- `validation_status=ready`
- `revision_match=true`

This document does not contain information about employee benefits, purchasing, legal policy, public safety procedure, or any real organization.
