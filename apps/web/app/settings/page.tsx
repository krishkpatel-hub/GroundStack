import { AppFrame } from "@/components/app-frame";

const settings = [
  [
    "Authentication",
    "Production uses provider-neutral OIDC with Authorization Code and PKCE.",
  ],
  [
    "Demo access",
    "Anonymous demo chat is quota-limited and cannot mutate the knowledge base.",
  ],
  [
    "Knowledge base",
    "The current corpus is shared and admin-managed, not tenant-isolated.",
  ],
  [
    "Feedback",
    "Feedback can create training candidates, but review is required before export.",
  ],
  [
    "Observability",
    "Detailed metrics require an internal token or admin access.",
  ],
];

export default function SettingsPage() {
  return (
    <AppFrame
      title="Model and system settings"
      description="Review runtime controls and production-hardening decisions. Configuration changes are handled through deployment environment variables."
    >
      <section className="section-band">
        <h2 className="section-title">Operational policy</h2>
        <div className="table-wrap mt-4">
          <table className="data-table">
            <caption>GroundStack system settings summary</caption>
            <thead>
              <tr>
                <th>Area</th>
                <th>Current behavior</th>
              </tr>
            </thead>
            <tbody>
              {settings.map(([area, detail]) => (
                <tr key={area}>
                  <td>{area}</td>
                  <td>{detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="section-band mt-6">
        <h2 className="section-title">Unavailable from the browser</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--graphite)]">
          Provider credentials, model endpoint secrets, database URLs, and
          metrics tokens are intentionally not exposed to the frontend. Use
          deployment configuration and the documented runbooks for operational
          changes.
        </p>
      </section>
    </AppFrame>
  );
}
