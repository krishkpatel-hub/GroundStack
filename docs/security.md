# Security Summary

- API authorization protects document upload, inspection, retry, and deletion.
- Development identity headers are accepted only in explicit development mode.
- Production settings reject the development bypass, wildcard CORS, wildcard trusted hosts,
  insecure session cookies, and missing identity configuration.
- File ingestion validates extension, MIME type, size, and content.
- URL ingestion rejects credentials, private addresses, unsafe redirects, unexpected content
  types, and hosts outside the administrator allowlist.
- Uploaded text is untrusted evidence and cannot replace the system prompt.
- Citation validation rejects source IDs that were not retrieved.
- Secrets, uploads, database volumes, generated output, and model artifacts are ignored by Git
  and checked by the repository scanner.

See [security/THREAT_MODEL.md](security/THREAT_MODEL.md) and
[security/AI_SECURITY_REVIEW.md](security/AI_SECURITY_REVIEW.md).
