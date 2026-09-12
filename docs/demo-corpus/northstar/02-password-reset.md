# Northstar Systems Password Reset Procedure

Category: Account Access
Version: NS-AUTH-2.1
Updated: 2026-08-16
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Self-Service Reset

Employees reset forgotten passwords through **Northstar Identity Portal** at `identity.northstar.example`.

1. Select **Forgot password**.
2. Enter your company username, not your email alias.
3. Complete one approved multi-factor challenge.
4. Create a password with at least 14 characters.
5. Wait two minutes before retrying VPN, email, or SSO login.

## Help Desk Reset

The help desk may issue a temporary password only after verifying employee ID, manager name, and device serial number. Temporary passwords expire after 30 minutes and must be changed at first login.

## Lockout Codes

- `AUTH-LOCK-15`: too many failed attempts in 15 minutes. Wait 15 minutes or request help desk unlock.
- `AUTH-RESET-EXPIRED`: reset link expired. Start a new self-service reset.
- `AUTH-POLICY-22`: proposed password matches a blocked pattern.

## Scope Limit

This document covers account password reset only. It does not define HR, payroll, or benefits procedures.
