import {
  ArrowRight,
  BookOpen,
  FileUp,
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
      description="A technical-support assistant that answers questions from approved documentation and shows the sources it used."
      actions={
        <div className="flex flex-wrap gap-2">
          <Link className="button button-primary no-underline" href="/ask">
            <MessageSquare className="h-4 w-4" aria-hidden />
            Ask a question
          </Link>
          <Link className="button no-underline" href="/knowledge">
            <FileUp className="h-4 w-4" aria-hidden />
            Manage documents
          </Link>
        </div>
      }
    >
      <div className="landing-grid">
        <section className="landing-intro" aria-labelledby="landing-heading">
          <h2 id="landing-heading" className="landing-title">
            Ask technical questions and get answers from uploaded documents.
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-7 text-[var(--graphite-strong)]">
            GroundStack helps support teams keep answers tied to an approved
            knowledge base. An administrator adds documentation, users ask
            questions, and every answer shows the document excerpts that support
            it.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="button button-primary no-underline" href="/ask">
              Ask a question
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
            <Link className="button no-underline" href="/about">
              How it works
            </Link>
            <Link className="button no-underline" href="/knowledge">
              Manage documents
            </Link>
          </div>
        </section>

        <section
          aria-labelledby="capabilities-heading"
          className="section-band"
        >
          <h2 id="capabilities-heading" className="section-title">
            Three-step workflow
          </h2>
          <div className="feature-grid mt-4">
            <article>
              <FileUp className="h-5 w-5" aria-hidden />
              <h3>1. Add documentation</h3>
              <p>
                Authorized administrators upload approved technical documents
                that become the knowledge base.
              </p>
            </article>
            <article>
              <MessageSquare className="h-5 w-5" aria-hidden />
              <h3>2. Ask a technical question</h3>
              <p>
                Users ask questions in plain language after documentation has
                been added.
              </p>
            </article>
            <article>
              <BookOpen className="h-5 w-5" aria-hidden />
              <h3>3. Review answer and sources</h3>
              <p>
                GroundStack displays an answer plus the real source excerpts it
                used.
              </p>
            </article>
          </div>
        </section>

        <section
          aria-labelledby="architecture-heading"
          className="section-band"
        >
          <h2 id="architecture-heading" className="section-title">
            What happens behind the scenes
          </h2>
          <ol className="pipeline-list mt-4">
            <li>
              Administrators upload Markdown, text, HTML, PDF, or an allowed
              documentation URL.
            </li>
            <li>
              The backend validates the source, extracts text, splits it into
              chunks, and stores searchable records in PostgreSQL with pgvector.
            </li>
            <li>
              A question retrieves relevant chunks from the uploaded
              documentation.
            </li>
            <li>
              The answer is accepted only when its citations match returned
              sources. Unsupported questions receive an insufficient-evidence
              response.
            </li>
          </ol>
        </section>

        <section aria-labelledby="examples-heading" className="section-band">
          <h2 id="examples-heading" className="section-title">
            Example questions
          </h2>
          <p className="mt-2 text-sm leading-6 text-[var(--graphite)]">
            These examples work after the included fictional demo document has
            been uploaded.
          </p>
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
            <Link href="/about">How it works</Link>
            <Link href="/sources">Sources</Link>
            <Link href="/settings">Health check</Link>
          </div>
        </section>
      </div>
    </AppFrame>
  );
}
