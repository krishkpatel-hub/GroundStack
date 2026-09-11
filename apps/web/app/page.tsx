import type { Metadata } from "next";
import Link from "next/link";

import { BrandMark } from "@/components/brand-mark";

export const metadata: Metadata = {
  title: "GroundStack | Source-backed technical answers",
  description:
    "Ask questions against approved technical documentation and inspect the sources supporting every answer.",
  openGraph: {
    title: "GroundStack | Source-backed technical answers",
    description:
      "Ask questions against approved technical documentation and inspect the sources supporting every answer.",
    type: "website",
  },
};

const steps = [
  [
    "Add documentation",
    "Upload approved technical files or allowed docs URLs.",
  ],
  ["Ask a question", "Use plain language to ask about the knowledge base."],
  ["Review sources", "Inspect the document excerpts behind each answer."],
] as const;

export default function Home() {
  return (
    <div className="public-page">
      <header className="public-header">
        <Link href="/" className="text-inherit no-underline">
          <BrandMark />
        </Link>
        <nav className="public-nav" aria-label="Public navigation">
          <Link href="/about">Project details</Link>
        </nav>
      </header>

      <main className="public-main">
        <section className="public-hero" aria-labelledby="hero-title">
          <h1 id="hero-title">
            Ask technical questions. Get answers backed by your documentation.
          </h1>
          <p>
            GroundStack searches approved technical documents and returns
            answers with sources you can inspect.
          </p>
          <div className="public-actions">
            <Link className="button button-primary no-underline" href="/ask">
              Open workspace
            </Link>
            <Link className="button no-underline" href="#how-it-works">
              How it works
            </Link>
          </div>
        </section>

        <section
          id="how-it-works"
          className="public-section"
          aria-labelledby="workflow-title"
        >
          <h2 id="workflow-title">How it works</h2>
          <ol className="workflow-steps">
            {steps.map(([title, body]) => (
              <li key={title}>
                <h3>{title}</h3>
                <p>{body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section
          className="public-section narrow"
          aria-labelledby="sources-title"
        >
          <h2 id="sources-title">Source-backed answers</h2>
          <p>
            GroundStack keeps the answer and its supporting document excerpts
            together, so a reviewer can check whether the response is supported
            by the available material.
          </p>
        </section>
      </main>

      <footer className="public-footer">
        <span>GroundStack portfolio project</span>
        <Link href="/about">Project details</Link>
      </footer>
    </div>
  );
}
