import { AppFrame } from "@/components/app-frame";

export default function DiscordTermsPage() {
  return (
    <AppFrame
      title="Discord terms"
      description="GroundStack Discord usage terms for sandbox and demo deployments."
    >
      <section className="section-band space-y-4">
        <p className="text-sm leading-6 text-[var(--graphite-strong)]">
          GroundStack provides AI-generated answers from configured knowledge
          sources. Answers may be incomplete, should be checked against
          citations, and are not a substitute for a human maintainer when the
          answer is uncertain or high impact.
        </p>
        <p className="text-sm leading-6 text-[var(--graphite-strong)]">
          Community members may use `/ask` for explicit technical-support
          questions. GroundStack does not monitor normal messages, does not send
          unsolicited direct messages, and does not use Discord records for
          model training.
        </p>
        <p className="text-sm leading-6 text-[var(--graphite-strong)]">
          For security or deletion requests, contact the repository owner
          through the published project contact channel or run `/delete-my-data`
          from the connected Discord server.
        </p>
      </section>
    </AppFrame>
  );
}
