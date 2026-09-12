import type { Metadata } from "next";
import Link from "next/link";

import { BrandMark } from "@/components/brand-mark";

export const metadata: Metadata = {
  title: "GroundStack | Private support knowledge assistant",
  description:
    "A portfolio demo of a private technical-support assistant that answers from approved documentation with inspectable citations.",
  openGraph: {
    title: "GroundStack | Private support knowledge assistant",
    description:
      "A portfolio demo of a private technical-support assistant that answers from approved documentation with inspectable citations.",
    type: "website",
  },
};

const steps = [
  [
    "Seed or upload approved docs",
    "The demo uses fictional Northstar Systems support documentation.",
  ],
  ["Ask a support question", "Employees ask about VPN, access, incidents, deployments, and API issues."],
  ["Review source evidence", "Every supported answer links back to the document excerpts that justify it."],
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
            A private technical-support assistant for approved documentation.
          </h1>
          <p>
            GroundStack demonstrates how employees can ask operational support
            questions and get answers grounded in a controlled knowledge base,
            with citations that reviewers can inspect.
          </p>
          <p className="demo-disclaimer">
            Demo workspace: Northstar Systems is fictional and uses original
            synthetic documentation. No customer usage is claimed.
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
            GroundStack separates generated answers from source evidence. If
            the Northstar demo corpus does not cover a question, the assistant
            should say it lacks enough evidence instead of inventing a policy.
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
