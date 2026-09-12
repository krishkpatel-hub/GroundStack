import Link from "next/link";

import { AppFrame } from "@/components/app-frame";

export default function AboutPage() {
  return (
    <AppFrame
      title="Documentation and about"
      description="A concise guide to the document-grounded support workflow."
    >
      <div className="landing-grid">
        <section className="section-band">
          <h2 className="section-title">How GroundStack works</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--graphite-strong)]">
            GroundStack ingests project-authored technical documentation, stores
            immutable document versions, retrieves relevant source chunks, and
            streams answers that cite the evidence used.
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
              Document administration is available only to authorized users.
            </li>
            <li>
              Questions outside the uploaded documents return an
              insufficient-evidence answer instead of an unsupported claim.
            </li>
          </ul>
        </section>
        <section className="section-band">
          <h2 className="section-title">Project documentation</h2>
          <div className="mt-3 flex flex-wrap gap-3 text-sm">
            <Link href="/knowledge">Manage documents</Link>
            <Link href="/settings">Security policy summary</Link>
          </div>
        </section>
      </div>
    </AppFrame>
  );
}
