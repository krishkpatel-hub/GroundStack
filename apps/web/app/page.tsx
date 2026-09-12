import type { Metadata } from "next";
import Link from "next/link";

import { BrandMark } from "@/components/brand-mark";
import {
  HeroWorkflow,
  LandingWorkflowTabs,
} from "@/components/landing-experience";

export const metadata: Metadata = {
  title: "GroundStack | Answers grounded in trusted documents",
  description:
    "GroundStack answers questions from approved organizational documentation and shows the evidence behind every supported response.",
  openGraph: {
    title: "GroundStack | Answers grounded in trusted documents",
    description:
      "GroundStack answers questions from approved organizational documentation and shows the evidence behind every supported response.",
    type: "website",
  },
};

const capabilities = [
  {
    title: "Controlled knowledge",
    body: "Answers are based on documentation intentionally added to the organization’s knowledge base.",
    visual: (
      <div className="capability-visual" aria-hidden="true">
        <span className="mini-label">Approved sources</span>
        <div className="mini-document-row">
          <span>Support procedures.pdf</span>
          <strong>Ready</strong>
        </div>
        <div className="mini-document-row">
          <span>API guide.md</span>
          <strong>Ready</strong>
        </div>
      </div>
    ),
  },
  {
    title: "Inspectable evidence",
    body: "Citations connect supported claims to the relevant source document and excerpt.",
    visual: (
      <div className="capability-visual" aria-hidden="true">
        <span className="mini-label">Source [S1]</span>
        <p className="mini-excerpt">
          Confirm the active configuration revision before restarting the
          service.
        </p>
      </div>
    ),
  },
  {
    title: "Honest limitations",
    body: "When retrieved evidence does not support an answer, GroundStack reports that limitation clearly.",
    visual: (
      <div className="capability-visual" aria-hidden="true">
        <span className="mini-label">Evidence check</span>
        <p className="mini-limitation">
          Not enough evidence in the approved documents.
        </p>
      </div>
    ),
  },
  {
    title: "Managed sources",
    body: "Authorized users can upload, inspect, retry, and remove documents from one workspace.",
    visual: (
      <div className="capability-visual" aria-hidden="true">
        <span className="mini-label">Document activity</span>
        <div className="mini-status-line">
          <span className="mini-status-dot" />
          Processing complete
        </div>
      </div>
    ),
  },
] as const;

export default function Home() {
  return (
    <div className="public-page">
      <div className="landing-top">
        <header className="public-header">
          <div className="landing-container landing-header-inner">
            <Link
              href="/"
              className="landing-brand text-inherit no-underline"
              aria-label="GroundStack home"
            >
              <BrandMark />
            </Link>
            <nav className="landing-nav" aria-label="Public navigation">
              <Link href="#how-it-works">How it works</Link>
              <Link href="#capabilities">Capabilities</Link>
              <Link href="#security">Security</Link>
              <Link className="landing-nav-action" href="/ask">
                Open workspace
              </Link>
            </nav>
          </div>
        </header>

        <main>
          <section className="public-hero" aria-labelledby="hero-title">
            <div className="landing-container hero-grid">
              <div className="hero-copy">
                <p className="landing-eyebrow">Private knowledge support</p>
                <h1 id="hero-title">
                  Answers grounded in the documents your organization trusts.
                </h1>
                <p className="hero-summary">
                  Upload approved documentation, ask questions in natural
                  language, and inspect the exact sources behind every supported
                  answer.
                </p>
                <div className="public-actions">
                  <Link
                    className="landing-action landing-action-primary"
                    href="/ask"
                  >
                    Open workspace
                  </Link>
                  <Link
                    className="landing-action landing-action-secondary"
                    href="#how-it-works"
                  >
                    See how it works
                  </Link>
                </div>
                <p className="hero-trust">
                  Designed to answer from approved sources—and say when the
                  evidence is not enough.
                </p>
              </div>
              <HeroWorkflow />
            </div>
          </section>
        </main>
      </div>

      <section
        id="how-it-works"
        className="landing-section landing-workflow-section"
        aria-labelledby="workflow-title"
      >
        <div className="landing-container">
          <div className="landing-section-heading">
            <p className="landing-eyebrow landing-eyebrow-light">
              How GroundStack works
            </p>
            <h2 id="workflow-title">
              From documentation to a supported answer.
            </h2>
            <p>
              GroundStack turns approved source material into searchable
              evidence, then uses that evidence to guide each response.
            </p>
          </div>
          <LandingWorkflowTabs />
        </div>
      </section>

      <section
        id="capabilities"
        className="landing-section landing-capabilities"
        aria-labelledby="capabilities-title"
      >
        <div className="landing-container">
          <div className="landing-section-heading">
            <p className="landing-eyebrow landing-eyebrow-light">
              Product capabilities
            </p>
            <h2 id="capabilities-title">
              A focused workflow for trusted answers.
            </h2>
          </div>
          <div className="capability-list">
            {capabilities.map((capability, index) => (
              <article className="capability-row" key={capability.title}>
                <div className="capability-copy">
                  <span className="capability-index" aria-hidden="true">
                    0{index + 1}
                  </span>
                  <h3>{capability.title}</h3>
                  <p>{capability.body}</p>
                </div>
                {capability.visual}
              </article>
            ))}
          </div>
        </div>
      </section>

      <section
        id="security"
        className="landing-section landing-security"
        aria-labelledby="security-title"
      >
        <div className="landing-container security-grid">
          <div>
            <p className="landing-eyebrow landing-eyebrow-light">
              Security and privacy
            </p>
            <h2 id="security-title">Built around controlled sources.</h2>
          </div>
          <p>
            GroundStack separates application instructions from uploaded
            content, validates returned citations, and protects
            document-management actions through server-side authorization.
            Actual privacy depends on the selected hosting and model-provider
            configuration.
          </p>
        </div>
      </section>

      <section className="landing-final-cta" aria-labelledby="cta-title">
        <div className="landing-container final-cta-inner">
          <div>
            <h2 id="cta-title">
              Turn trusted documentation into answers people can verify.
            </h2>
            <p>
              Add an approved source, ask a question, and inspect the evidence
              behind the response.
            </p>
          </div>
          <Link className="landing-action landing-action-primary" href="/ask">
            Open GroundStack
          </Link>
        </div>
      </section>

      <footer className="public-footer">
        <div className="landing-container public-footer-inner">
          <span>GroundStack portfolio project</span>
          <Link href="/about">Project details</Link>
        </div>
      </footer>
    </div>
  );
}
