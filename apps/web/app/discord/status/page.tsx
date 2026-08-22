import { AppFrame } from "@/components/app-frame";

export default function DiscordStatusPage() {
  return (
    <AppFrame
      title="Discord status"
      description="Integration readiness and operating boundaries for the GroundStack Discord assistant."
    >
      <section className="section-band">
        <dl className="metric-grid">
          <div>
            <dt>Message access</dt>
            <dd>Slash commands only</dd>
          </div>
          <div>
            <dt>DMs</dt>
            <dd>Disabled by default</dd>
          </div>
          <div>
            <dt>Message Content intent</dt>
            <dd>Not required</dd>
          </div>
          <div>
            <dt>Training eligibility</dt>
            <dd>Discord data excluded</dd>
          </div>
        </dl>
        <p className="mt-5 text-sm leading-6 text-[var(--graphite-strong)]">
          This repository implements the local integration path. Bot
          installation, command registration, and production operation require
          explicit owner approval and securely configured Discord credentials.
        </p>
      </section>
    </AppFrame>
  );
}
