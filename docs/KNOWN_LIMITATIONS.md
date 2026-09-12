# Known Limitations

- No real organization, customer, production traffic, uptime, or performance result is claimed.
- The local development identity is not production authentication.
- The knowledge base is shared rather than tenant-isolated.
- A hosted model provider receives the evidence excerpts included in its prompt.
- Local rate and capacity counters are process-scoped and intended for one API instance.
- Document processing runs in the API process rather than a durable worker.
- PDF extraction supports text-based PDFs; scanned documents require external OCR.
- URL ingestion is disabled unless administrators configure an explicit hostname allowlist.
- The semantic relevance threshold is fixed and should be calibrated against an approved corpus.
- Browser tests mock the API, and backend provider tests use deterministic output.
- Real provider quality, latency, cost, and availability require a private provider configuration
  and a separate smoke test.
