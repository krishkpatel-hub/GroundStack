import Link from "next/link";

import { AppFrame } from "@/components/app-frame";

export default function AboutPage() {
  return (
    <AppFrame
      title="Documentation and about"
      description="A concise guide to how GroundStack retrieves, answers, evaluates, and improves."
    >
      <div className="landing-grid">
        <section className="section-band">
          <h2 className="section-title">How GroundStack works</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--graphite-strong)]">
            GroundStack ingests project-authored technical documentation, stores
            immutable document versions, retrieves source chunks with hybrid
            search, and streams answers that must cite validated evidence.
          </p>
        </section>
        <section className="section-band">
          <h2 className="section-title">Safety decisions</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-[var(--graphite-strong)]">
            <li>
              Source text is treated as untrusted evidence, never instructions.
            </li>
            <li>
              Generated citations are validated before an answer is presented as
              grounded.
            </li>
            <li>
              Anonymous demo users cannot upload, evaluate, train, or change
              settings.
            </li>
            <li>Feedback-derived training examples require human review.</li>
          </ul>
        </section>
        <section className="section-band">
          <h2 className="section-title">Project documentation</h2>
          <div className="mt-3 flex flex-wrap gap-3 text-sm">
            <Link href="/sources">Source inventory</Link>
            <Link href="/evaluation">Evaluation dashboard</Link>
            <Link href="/settings">Security policy summary</Link>
          </div>
        </section>
      </div>
    </AppFrame>
  );
}
