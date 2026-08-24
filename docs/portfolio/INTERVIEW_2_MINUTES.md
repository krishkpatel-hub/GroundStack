# Two-Minute Interview Story

GroundStack started as a technical-support RAG application and grew into a release-candidate system.
The core design separates retrieval from generation: retrieval finds and ranks source chunks, while
generation can only answer from the selected evidence. Citation validation rejects malformed,
fabricated, or unsupported citations, and an empty retrieval result produces an insufficient-evidence
answer instead of a guess.

The backend is FastAPI with async SQLAlchemy, PostgreSQL, pgvector, Alembic migrations, and
provider-neutral LLM interfaces. The frontend is a Next.js admin/product shell for asking questions,
inspecting citations, managing sources, reviewing evaluations and training candidates, and handling
Discord escalations. Discord support uses application commands only; it verifies signed interactions
and does not scan ordinary messages.

The final milestone focused on release discipline: threat modeling against the OWASP GenAI LLM Top
10 2026 guidance, secret/dependency checks, benchmark evidence, claims review, runbooks, and a
recruiter-ready portfolio package. I intentionally do not claim production usage, live Discord
adoption, complete OWASP compliance, or real fine-tuning results without evidence.
