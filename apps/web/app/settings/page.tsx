import { AppFrame } from "@/components/app-frame";

const settings = [
  [
    "Authentication",
    "Document management is enforced by the API and requires an administrator identity.",
  ],
  [
    "Local development",
    "The documented development identity is available only when APP_ENV=development.",
  ],
  [
    "Knowledge base",
    "The current corpus is shared and admin-managed, not tenant-isolated.",
  ],
  ["Feedback", "Helpful and not-helpful ratings are stored with the answer."],
];

export default function SettingsPage() {
  return (
    <AppFrame
      title="System settings"
      description="Review the security and data boundaries used by this workspace."
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
          Provider credentials, model endpoint secrets, and database URLs are
          intentionally not exposed to the frontend. Use local environment
          configuration for operational changes.
        </p>
      </section>
    </AppFrame>
  );
}
