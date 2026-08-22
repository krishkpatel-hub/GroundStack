import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";

import { AppFrame } from "@/components/app-frame";

export default function Home() {
  const examples = [
    "How do I configure pgvector for GroundStack?",
    "Why did ingestion reject my documentation URL?",
    "What happens when there is not enough evidence?",
  ];

  return (
    <AppFrame
      title="GroundStack"
      description="A grounded technical-support assistant that retrieves source evidence, streams answers, and captures feedback for human-reviewed improvement."
      actions={
        <Link className="button button-primary no-underline" href="/ask">
          <MessageSquare className="h-4 w-4" aria-hidden />
          Ask a question
        </Link>
      }
    >
      <div className="landing-grid">
        <section className="landing-intro" aria-labelledby="landing-heading">
          <h2 id="landing-heading" className="landing-title">
            Grounded answers for developer support, with citations you can
            inspect.
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-7 text-[var(--graphite-strong)]">
            GroundStack combines an admin-managed knowledge base, hybrid
            retrieval, citation validation, and structured feedback so technical
            answers stay tied to available documentation.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="button button-primary no-underline" href="/ask">
              Ask a question
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
            <Link className="button no-underline" href="/about">
              How it works
            </Link>
          </div>
        </section>

        <section
          aria-labelledby="capabilities-heading"
          className="section-band"
        >
          <h2 id="capabilities-heading" className="section-title">
            What is available now
          </h2>
          <div className="feature-grid mt-4">
            <article>
              <MessageSquare className="h-5 w-5" aria-hidden />
              <h3>Grounded technical answers</h3>
              <p>
                Questions are answered from retrieved source chunks, not
                free-form claims.
              </p>
            </article>
            <article>
              <BookOpen className="h-5 w-5" aria-hidden />
              <h3>Inspectable citations</h3>
              <p>
                Each completed answer separates generated text from supporting
                sources.
              </p>
            </article>
            <article>
              <CheckCircle2 className="h-5 w-5" aria-hidden />
              <h3>Feedback-driven improvement</h3>
              <p>
                User feedback can become reviewed training candidates, never
                automatic data.
              </p>
            </article>
          </div>
        </section>

        <section
          aria-labelledby="architecture-heading"
          className="section-band"
        >
          <h2 id="architecture-heading" className="section-title">
            Compact architecture
          </h2>
          <ol className="pipeline-list mt-4">
            <li>
              Administrators ingest Markdown, text, HTML, PDF, or allowlisted
              URLs.
            </li>
            <li>
              GroundStack chunks, embeds, and indexes versions in PostgreSQL
              with pgvector.
            </li>
            <li>
              Hybrid retrieval and optional reranking select evidence for each
              question.
            </li>
            <li>
              The generator streams an answer and citation validation rejects
              unsupported output.
            </li>
          </ol>
        </section>

        <section aria-labelledby="examples-heading" className="section-band">
          <h2 id="examples-heading" className="section-title">
            Example questions
          </h2>
          <div className="mt-4 grid gap-2">
            {examples.map((question) => (
              <Link
                key={question}
                className="question-link"
                href={`/ask?q=${encodeURIComponent(question)}`}
              >
                {question}
              </Link>
            ))}
          </div>
        </section>

        <section aria-labelledby="limits-heading" className="section-band">
          <h2 id="limits-heading" className="section-title">
            Safety and limits
          </h2>
          <div className="mt-3 flex gap-3">
            <ShieldCheck className="mt-1 h-5 w-5 shrink-0" aria-hidden />
            <p className="max-w-3xl text-sm leading-6 text-[var(--graphite-strong)]">
              Answers are AI-generated and should be verified against the cited
              sources. The current product supports a shared admin-managed
              knowledge base; fully isolated multi-tenant knowledge workspaces
              are planned, not shipped.
            </p>
          </div>
          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <Link href="/about">Documentation</Link>
            <Link href="/sources">Sources</Link>
            <Link href="/settings">Security policy</Link>
          </div>
        </section>
      </div>
    </AppFrame>
  );
}
