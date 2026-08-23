# Interview Q&A

## Why not just fine-tune?

Fine-tuning does not guarantee current, source-specific answers. GroundStack uses RAG for evidence
and citations, while fine-tuning remains an offline workflow for reviewed examples.

## How do you reduce hallucinations?

The model receives bounded retrieved context and must cite retrieved IDs. GroundStack validates the
final answer and rejects unsupported or fabricated citations.

## What is actually tested?

Backend tests, frontend tests/build, migration checks, load-harness unit tests, and evaluation
runners are part of the repository. The benchmark evidence committed for Milestone 12 is a synthetic
dry-run; it is not a live capacity claim.

## What are the biggest limitations?

The knowledge base is shared, not tenant-isolated. There is no production deployment claim, no live
public Discord installation, and no completed real fine-tuning result.

## How is Discord privacy handled?

GroundStack processes only slash-command questions, verifies Discord signatures, uses HMAC user IDs,
encrypts temporary interaction tokens, disables DMs by default, and excludes Discord records from
training.

## What would you do next?

Run approved staging load tests, add durable workers, choose a license, enable GitHub security
settings, and create a final release only after review.
