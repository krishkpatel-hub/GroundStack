# Northstar Systems Employee Device Enrollment

Category: Device Management
Version: NS-DEVICE-2.6
Updated: 2026-08-23
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Enrollment Requirements

Employees must enroll laptops and phones before accessing VPN, email, or internal applications. The device must have disk encryption enabled, screen lock set to 10 minutes or less, and a supported operating system.

## Laptop Enrollment

1. Connect to a trusted network.
2. Open **Northstar Device Manager**.
3. Enter the enrollment code `NS-ENROLL-LAPTOP`.
4. Wait for policy status **Compliant**.
5. Reboot before starting VPN setup.

## Phone Enrollment

1. Install **Northstar Verify**.
2. Scan the QR code from the Identity Portal.
3. Approve device management.
4. Confirm status **Managed and Compliant**.

## Failure Codes

- `DEV-ENROLL-409`: device already assigned to another employee.
- `DEV-COMPLY-12`: missing disk encryption.
- `DEV-OS-OLD`: operating system below minimum supported version.
