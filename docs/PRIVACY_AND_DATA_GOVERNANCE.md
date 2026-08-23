# Privacy And Data Governance

Version: `1.0.0-rc.1`

## Data Processed

- Web app: questions, streamed answers, citations, conversation metadata, auth state, and admin UI
  inputs.
- API: request metadata, conversations, messages, feedback, generation runs, retrieval runs,
  ingestion jobs, evaluation records, training candidates, and metrics.
- RAG pipeline: admin-submitted source content, normalized text, chunks, checksums, embeddings, and
  citation metadata.
- Fine-tuning workflow: project-authored seed data, reviewed training candidates, manifests, and
  generated local reports. Discord data is excluded.
- Discord integration: signed interaction metadata, explicit slash-command question, encrypted
  temporary interaction token, HMAC user identifier, feedback, escalation, and deletion records.
- Logs/metrics: low-cardinality operational data. Questions, answers, user IDs, guild IDs, and
  request IDs must not be metric labels.

## Training Inclusion

Training data inclusion requires explicit human review. Public demo prompts and Discord feedback do
not become training data by default. Discord records are marked `source_platform=discord` and
`training_eligible=false`, and approval attempts are rejected.

## Deletion

- Conversation deletion removes the scoped conversation and messages where supported.
- Document/source removal is an admin operation; derived chunks and embeddings are part of the
  source/document lifecycle.
- Discord `/delete-my-data` deletes supported Discord feedback, escalations, interactions, jobs, and
  generated messages for the requesting HMAC user in that guild.
- Backup retention, provider logs, and external platform logs are operational responsibilities.

## Retention

Retention is controlled by environment and application settings. Discord control records use the
configured retention period and temporary interaction tokens are encrypted and cleared after
delivery. Public demo data should remain synthetic or explicitly approved.

## Limitations

GroundStack is not a production privacy platform. It does not yet implement tenant-isolated
knowledge bases, automated PII discovery, or provider-side log deletion.
