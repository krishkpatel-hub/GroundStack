# Interview Story

GroundStack was built to show how a developer-support AI tool can be useful without pretending the
model knows everything. The hardest part was making the answer pipeline disciplined: retrieve
evidence, trim context, generate with explicit citations, validate citation IDs, and abstain when
retrieval is insufficient.

RAG was the right foundation because support answers depend on source material that changes over
time. Fine-tuning can improve style or repeated patterns, but it cannot guarantee that a response is
grounded in the current approved corpus. The project therefore keeps fine-tuning as a reviewed,
provenance-controlled workflow rather than the primary knowledge store.

The most instructive failure was deployment polish. Local behavior was not enough: Compose exposed
configuration issues around list-style environment variables, container host binding, and Caddy
defaults. Fixing those made the project more credible because the deployment path now has explicit
checks and documented tradeoffs.
