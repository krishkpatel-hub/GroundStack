"use client";

import { Bot, Check, RefreshCw, Save, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { AppFrame } from "@/components/app-frame";
import {
  fetchDiscordEscalations,
  fetchDiscordGuildConfig,
  updateDiscordEscalation,
  updateDiscordGuildConfig,
  type DiscordEscalation,
  type DiscordGuildConfig,
} from "@/lib/discord";

const statusOptions = [
  "open",
  "assigned",
  "resolved",
  "duplicate",
  "out_of_scope",
];

export function DiscordAdmin() {
  const [guildId, setGuildId] = useState("");
  const [config, setConfig] = useState<DiscordGuildConfig | null>(null);
  const [channels, setChannels] = useState("");
  const [escalations, setEscalations] = useState<DiscordEscalation[]>([]);
  const [selected, setSelected] = useState<DiscordEscalation | null>(null);
  const [assignedTo, setAssignedTo] = useState("");
  const [humanResponse, setHumanResponse] = useState("");
  const [status, setStatus] = useState<DiscordEscalation["status"]>("open");
  const [deliveryStatus, setDeliveryStatus] =
    useState<DiscordEscalation["delivery_status"]>("pending");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadEscalations(filter?: string) {
    const rows = await fetchDiscordEscalations(filter);
    setEscalations(rows);
    setSelected(rows[0] ?? null);
    setAssignedTo(rows[0]?.assigned_to ?? "");
    setHumanResponse(rows[0]?.human_response ?? "");
    setStatus(rows[0]?.status ?? "open");
    setDeliveryStatus(rows[0]?.delivery_status ?? "pending");
  }

  async function loadConfig() {
    if (!guildId.trim()) return;
    setLoading(true);
    try {
      const row = await fetchDiscordGuildConfig(guildId.trim());
      setConfig(row);
      setChannels(row.allowed_channel_ids.join("\n"));
      setError(null);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Discord config load failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function saveConfig() {
    if (!config) return;
    const updated = await updateDiscordGuildConfig(config.guild_id, {
      enabled: config.enabled,
      allowed_channel_ids: channels
        .split(/\s+/)
        .map((item) => item.trim())
        .filter(Boolean),
      moderator_channel_id: config.moderator_channel_id || null,
      default_visibility: config.default_visibility,
      per_user_limit_per_minute: config.per_user_limit_per_minute,
      per_channel_limit_per_minute: config.per_channel_limit_per_minute,
      per_guild_limit_per_minute: config.per_guild_limit_per_minute,
      daily_capacity: config.daily_capacity,
      thread_behavior: config.thread_behavior,
      retention_days: config.retention_days,
      enabled_commands: config.enabled_commands,
    });
    setConfig(updated);
    setChannels(updated.allowed_channel_ids.join("\n"));
  }

  async function saveEscalation() {
    if (!selected) return;
    const updated = await updateDiscordEscalation(selected.id, {
      status,
      assigned_to: assignedTo || null,
      human_response: humanResponse || null,
      delivery_status: deliveryStatus,
    });
    setEscalations((current) =>
      current.map((item) => (item.id === updated.id ? updated : item)),
    );
    setSelected(updated);
  }

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadEscalations("open").catch((loadError) =>
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Discord escalation load failed",
        ),
      );
    }, 0);
    return () => window.clearTimeout(timeout);
  }, []);

  const evidencePreview = useMemo(() => {
    if (!selected) return "No escalation selected.";
    return JSON.stringify(selected.citations, null, 2);
  }, [selected]);

  return (
    <AppFrame
      title="Discord integration"
      description="Manage slash-command server access, escalation review, and privacy-safe Discord records."
      actions={
        <button
          className="button"
          type="button"
          onClick={() => void loadEscalations()}
        >
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh
        </button>
      }
    >
      <section className="space-y-6">
        {error && <div className="inline-alert">{error}</div>}
        <section
          className="section-band"
          aria-labelledby="discord-config-heading"
        >
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-64 flex-1">
              <label htmlFor="discord-guild-id" className="label">
                Guild ID
              </label>
              <input
                id="discord-guild-id"
                className="field"
                value={guildId}
                onChange={(event) => setGuildId(event.target.value)}
                placeholder="Discord server ID"
              />
            </div>
            <button
              className="button"
              type="button"
              onClick={() => void loadConfig()}
            >
              <Bot className="h-4 w-4" aria-hidden />
              Load
            </button>
          </div>
          {loading && (
            <p className="mt-3 text-sm text-[var(--graphite)]">
              Loading Discord config.
            </p>
          )}
          {config && (
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              <div>
                <h2 id="discord-config-heading" className="section-title">
                  Server controls
                </h2>
                <dl className="document-facts mt-4">
                  <div>
                    <dt>Enabled</dt>
                    <dd>
                      <input
                        type="checkbox"
                        checked={config.enabled}
                        onChange={(event) =>
                          setConfig({
                            ...config,
                            enabled: event.target.checked,
                          })
                        }
                        aria-label="Enable GroundStack for this Discord server"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>Default visibility</dt>
                    <dd>
                      <select
                        className="field"
                        value={config.default_visibility}
                        onChange={(event) =>
                          setConfig({
                            ...config,
                            default_visibility: event.target.value as
                              "public" | "private",
                          })
                        }
                      >
                        <option value="private">private</option>
                        <option value="public">public</option>
                      </select>
                    </dd>
                  </div>
                  <div>
                    <dt>Thread behavior</dt>
                    <dd>
                      <select
                        className="field"
                        value={config.thread_behavior}
                        onChange={(event) =>
                          setConfig({
                            ...config,
                            thread_behavior: event.target.value as
                              "none" | "thread",
                          })
                        }
                      >
                        <option value="none">none</option>
                        <option value="thread">thread</option>
                      </select>
                    </dd>
                  </div>
                </dl>
                <label
                  htmlFor="discord-allowed-channels"
                  className="label mt-4"
                >
                  Allowed channels
                </label>
                <textarea
                  id="discord-allowed-channels"
                  className="field min-h-28"
                  value={channels}
                  onChange={(event) => setChannels(event.target.value)}
                />
                <label
                  htmlFor="discord-moderator-channel"
                  className="label mt-4"
                >
                  Moderator channel
                </label>
                <input
                  id="discord-moderator-channel"
                  className="field"
                  value={config.moderator_channel_id ?? ""}
                  onChange={(event) =>
                    setConfig({
                      ...config,
                      moderator_channel_id: event.target.value,
                    })
                  }
                />
              </div>
              <div>
                <h2 className="section-title">Limits and retention</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {[
                    ["per_user_limit_per_minute", "Per user/min"],
                    ["per_channel_limit_per_minute", "Per channel/min"],
                    ["per_guild_limit_per_minute", "Per guild/min"],
                    ["daily_capacity", "Daily capacity"],
                    ["retention_days", "Retention days"],
                  ].map(([field, label]) => (
                    <label key={field} className="label">
                      {label}
                      <input
                        className="field mt-1"
                        type="number"
                        min={1}
                        value={Number(
                          config[field as keyof DiscordGuildConfig],
                        )}
                        onChange={(event) =>
                          setConfig({
                            ...config,
                            [field]: Number(event.target.value),
                          })
                        }
                      />
                    </label>
                  ))}
                </div>
                <button
                  className="button button-primary mt-4"
                  type="button"
                  onClick={() => void saveConfig()}
                >
                  <Save className="h-4 w-4" aria-hidden />
                  Save server config
                </button>
              </div>
            </div>
          )}
        </section>

        <section
          className="two-column"
          aria-labelledby="discord-escalations-heading"
        >
          <div className="table-wrap">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 id="discord-escalations-heading" className="section-title">
                Escalations
              </h2>
              <select
                className="field max-w-44"
                defaultValue="open"
                onChange={(event) => void loadEscalations(event.target.value)}
                aria-label="Escalation status filter"
              >
                <option value="">all</option>
                {statusOptions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </div>
            <table className="data-table">
              <caption>Discord human escalation queue</caption>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Request</th>
                  <th>Delivery</th>
                </tr>
              </thead>
              <tbody>
                {escalations.map((item) => (
                  <tr
                    key={item.id}
                    className={selected?.id === item.id ? "selected-row" : ""}
                  >
                    <td>
                      <button
                        className="button min-h-9"
                        type="button"
                        onClick={() => {
                          setSelected(item);
                          setAssignedTo(item.assigned_to ?? "");
                          setHumanResponse(item.human_response ?? "");
                          setStatus(item.status);
                          setDeliveryStatus(item.delivery_status);
                        }}
                      >
                        {item.status}
                      </button>
                    </td>
                    <td>{item.request_id}</td>
                    <td>{item.delivery_status}</td>
                  </tr>
                ))}
                {escalations.length === 0 && (
                  <tr>
                    <td colSpan={3}>
                      No Discord escalations match this filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <section
            className="section-band"
            aria-labelledby="discord-escalation-detail"
          >
            <h2 id="discord-escalation-detail" className="section-title">
              Escalation detail
            </h2>
            {selected ? (
              <div className="mt-4">
                <p className="text-sm leading-6">{selected.question}</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <label className="label">
                    Status
                    <select
                      className="field mt-1"
                      value={status}
                      onChange={(event) =>
                        setStatus(
                          event.target.value as DiscordEscalation["status"],
                        )
                      }
                    >
                      {statusOptions.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="label">
                    Delivery
                    <select
                      className="field mt-1"
                      value={deliveryStatus}
                      onChange={(event) =>
                        setDeliveryStatus(
                          event.target
                            .value as DiscordEscalation["delivery_status"],
                        )
                      }
                    >
                      <option value="pending">pending</option>
                      <option value="delivered">delivered</option>
                      <option value="failed">failed</option>
                    </select>
                  </label>
                </div>
                <label htmlFor="discord-assignee" className="label mt-4">
                  Assigned to
                </label>
                <input
                  id="discord-assignee"
                  className="field"
                  value={assignedTo}
                  onChange={(event) => setAssignedTo(event.target.value)}
                />
                <label htmlFor="discord-human-response" className="label mt-4">
                  Human response
                </label>
                <textarea
                  id="discord-human-response"
                  className="field min-h-32"
                  value={humanResponse}
                  onChange={(event) => setHumanResponse(event.target.value)}
                />
                <pre className="pre-panel mt-4">{evidencePreview}</pre>
                <button
                  className="button button-primary mt-4"
                  type="button"
                  onClick={() => void saveEscalation()}
                >
                  <Check className="h-4 w-4" aria-hidden />
                  Save escalation
                </button>
              </div>
            ) : (
              <p className="mt-3 text-sm text-[var(--graphite)]">
                Select an escalation to inspect evidence and record a
                human-written response.
              </p>
            )}
          </section>
        </section>

        <p className="status-label">
          <ShieldCheck className="h-4 w-4" aria-hidden />
          Discord records remain `training_eligible=false` and are excluded from
          model training.
        </p>
      </section>
    </AppFrame>
  );
}
