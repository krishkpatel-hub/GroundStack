# GroundStack Project Summary

GroundStack is a portfolio-grade AI support application for answering technical questions with
retrieved evidence, visible citations, and evaluation artifacts. The system combines a Next.js
frontend, FastAPI backend, PostgreSQL with pgvector, hybrid retrieval, reranking, grounded generation,
feedback capture, and a fine-tuning preparation workflow.

The core engineering decision is to treat generation as the last step after retrieval and citation
selection. Fine-tuning is supported as a controlled workflow, but it does not replace retrieval
because answers need source-specific grounding and current documentation. The project also includes
auth boundaries, admin-only ingestion, evaluation dashboards, deployment guardrails, and public-demo
cost controls.

The Discord integration extends the same grounded pipeline to explicit slash commands. It verifies
signed interactions, queues encrypted jobs for a private worker, renders citation-aware Discord
answers, supports feedback and human escalation, and keeps Discord data out of model-training
workflows. The repository documents sandbox setup but does not claim a production Discord
installation.
