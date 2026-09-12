# Northstar Systems Access-Request Procedures

Category: Access Management
Version: NS-ACCESS-3.5
Updated: 2026-08-24
Demo note: Northstar Systems is a fictional organization for the GroundStack portfolio demo.

## Standard Access Request

Employees request access through the **Northstar Access Portal**. Every request needs a business reason, target system, role, manager approval, and expiration date.

## Analytics Database Access

To request access to the analytics database:

1. Open the Access Portal.
2. Select system **Analytics Database**.
3. Choose role **analytics_readonly** unless write access is approved by Data Operations.
4. Enter the project code and business reason.
5. Set an expiration date no longer than 90 days.
6. Submit for manager and Data Operations approval.

## Approval Rules

Production database roles require Data Operations approval. Admin roles require Security approval. Requests missing a business reason are rejected with code `ACCESS-REQ-400`.

## Revocation

Access is automatically reviewed every 90 days. Managers must remove access when an employee changes team or no longer needs the system.
