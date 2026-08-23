# Known Limitations

Version: `1.0.0-rc.1`

- GroundStack is not a production multi-tenant SaaS platform. The knowledge base is shared and
  admin-managed.
- No production deployment, public Discord installation, uptime, real-user volume, or hosted
  provider performance claim is made.
- Discord integration is implemented and mock-tested, but not installed into a live public server.
- Fine-tuning workflow is prepared and smoke-testable; no completed real LLaMA fine-tuning run is
  claimed.
- FastAPI background tasks remain process-local for ingestion in the local path. Durable queueing is
  a future production hardening item.
- Local benchmark evidence is synthetic and dry-run unless a timestamped `load/reports` artifact
  says otherwise.
- Docker/container verification may require local Docker daemon access and base-image network
  availability.
- Provider costs are estimates only unless actual billing evidence is supplied.
- OIDC logout clears local cookies; provider-side token revocation depends on the selected IdP.
- Data deletion is implemented for supported app-owned records, but backup retention and external
  provider logs remain operational responsibilities.
- There is no project license file yet. The repository owner must choose a license before a final
  public `v1.0.0` release.
