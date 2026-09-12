# Northstar Systems Employee VPN Setup and Troubleshooting

Category: Network Access
Version: NS-VPN-1.4
Updated: 2026-08-15
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Purpose

Employees use the Northstar VPN to reach private engineering, support, and analytics tools from managed devices. The approved client is **Northstar SecureConnect 5.8**.

## Setup Procedure

1. Open the device self-service portal and install **Northstar SecureConnect 5.8**.
2. Select the profile named **NS-CORP-FULL**.
3. Enter your Northstar username in the format `first.last`.
4. Approve the multi-factor prompt in **Northstar Verify**.
5. Confirm the status shows **Connected to gateway vpn-gw-02.northstar.example**.

## Troubleshooting

- If the client reports `VPN-201 profile missing`, reinstall the **NS-CORP-FULL** profile from self-service.
- If authentication loops more than twice, reset the local VPN profile and sign in again.
- If the gateway is unreachable, check the Service Status page for the component **Corporate VPN**.
- If split tunneling is needed, use profile **NS-CORP-SPLIT** only when Support approves ticket code `NET-ACCESS-SPLIT`.

## Escalation

Escalate to Network Support when `vpn-gw-02.northstar.example` is unreachable for more than 15 minutes or when more than five users report `VPN-504 gateway timeout`.
