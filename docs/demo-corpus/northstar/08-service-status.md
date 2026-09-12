# Northstar Systems Service-Status Troubleshooting

Category: Support Operations
Version: NS-STATUS-1.3
Updated: 2026-08-22
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Status Components

The status page tracks these components: Corporate VPN, Identity Portal, Support API, Analytics Database, Case Queue, and Device Enrollment.

## Troubleshooting Steps

1. Open `status.northstar.example`.
2. Check whether the affected component is listed as **Operational**, **Degraded**, or **Major Outage**.
3. Compare the component status with recent alerts in the support channel.
4. If the status page is stale for more than 10 minutes during an active outage, notify the incident commander.

## User Messaging

When a component is degraded, support replies should include the component name, current status, known workaround, and next update time. Do not promise a resolution time unless the incident commander has published one.

## Related Codes

- `STATUS-CACHE-10`: status page has not refreshed in 10 minutes.
- `STATUS-COMPONENT-MISSING`: support ticket references a component not tracked on the page.
