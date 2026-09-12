# Northstar Systems Multi-Factor Authentication Guide

Category: Account Security
Version: NS-MFA-3.0
Updated: 2026-08-17
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Approved Factors

Northstar supports these MFA factors:

- **Northstar Verify push** on an enrolled managed phone.
- **FIDO2 security key** registered in the Identity Portal.
- **Recovery code** generated from the Identity Portal.

SMS codes are not approved for production access.

## Enrollment

1. Sign in to `identity.northstar.example`.
2. Open **Security settings**.
3. Choose **Add factor**.
4. Register Northstar Verify or a FIDO2 key.
5. Save two recovery codes in the approved password manager.

## Troubleshooting

- If push approval does not arrive, confirm the phone is enrolled in device management.
- If a recovery code is used, generate a replacement code immediately.
- If a security key shows `MFA-FIDO-409`, remove the stale key record and register it again.

## Lost Device

Report a lost MFA device to Security Operations within one hour. The help desk can issue a temporary recovery code after identity verification.
