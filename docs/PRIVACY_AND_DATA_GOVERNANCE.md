# Privacy And Data Governance

GroundStack stores document text, chunks, embeddings, conversations, citations, and feedback
in the configured PostgreSQL database. Administrators must upload only material they are
authorized to process.

The provider boundary matters: when a hosted OpenAI-compatible model is configured, the
retrieved excerpts included in a generation request leave the application's infrastructure.
A self-hosted compatible model can reduce that exposure, but does not replace access control,
secure hosting, retention rules, encryption, backups, or incident response.

Normal logs use request IDs and operational metadata. They must not contain provider keys,
complete documents, or full private prompts. Retrieval-query persistence is disabled by
default.

Deleting a document removes its document records, chunks, and embeddings transactionally.
Old conversation answers may remain, but a deleted source must not be represented as currently
available evidence.

No private corpus or customer data is committed. The presentation validation file is original,
neutral content and is loaded only through an explicit administrator action.
