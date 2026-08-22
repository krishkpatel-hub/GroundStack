import { AppFrame } from "@/components/app-frame";

export default function DiscordPrivacyPage() {
  return (
    <AppFrame
      title="Discord privacy"
      description="GroundStack handles Discord data only from explicit slash-command interactions."
    >
      <section className="section-band space-y-4">
        <div>
          <h2 className="section-title">Data collected</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--graphite-strong)]">
            GroundStack stores the submitted slash-command question, guild and
            channel IDs needed for authorization, a keyed HMAC user identifier,
            delivery state, feedback, escalation records, and deletion requests.
            It does not collect member lists, presence, avatars, biographies,
            relationships, or ordinary channel history.
          </p>
        </div>
        <div>
          <h2 className="section-title">Training separation</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--graphite-strong)]">
            Discord records are marked with `source_platform=discord` and
            `training_eligible=false`. Feedback does not grant training
            permission, and Discord records are blocked from GroundStack
            training-candidate approval.
          </p>
        </div>
        <div>
          <h2 className="section-title">Deletion</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--graphite-strong)]">
            Users can run `/delete-my-data` and confirm the request from
            Discord. Server owners can disable or remove a guild configuration
            from the GroundStack admin interface.
          </p>
        </div>
      </section>
    </AppFrame>
  );
}
