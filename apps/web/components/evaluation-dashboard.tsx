"use client";

import { useEffect, useState } from "react";

import { AppFrame } from "@/components/app-frame";
import { fetchEvaluationRuns, type EvaluationRun } from "@/lib/evaluation";

export function EvaluationDashboard() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void fetchEvaluationRuns()
        .then(setRuns)
        .catch((loadError) =>
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Evaluation load failed",
          ),
        )
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timeout);
  }, []);

  const latest = runs[0];
  return (
    <AppFrame
      title="Evaluation"
      description="Inspect recorded GroundStack evaluation runs, deterministic metrics, and run manifests."
    >
      <section className="space-y-6">
        {loading && (
          <p className="text-sm text-[var(--graphite)]">
            Loading evaluation runs.
          </p>
        )}
        {error && <div className="inline-alert">{error}</div>}
        {!loading && runs.length === 0 && (
          <div className="empty-chat">
            <h2 className="section-title">No evaluation runs</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--graphite)]">
              Run the deterministic evaluation suite to record model, retrieval,
              and prompt behavior before promoting changes.
            </p>
          </div>
        )}
        {latest && (
          <section
            className="section-band"
            aria-labelledby="latest-eval-heading"
          >
            <h2 id="latest-eval-heading" className="section-title">
              Latest run summary
            </h2>
            <dl className="metric-grid mt-4">
              <div>
                <dt>Dataset</dt>
                <dd>{latest.dataset_version}</dd>
              </div>
              <div>
                <dt>Prompt</dt>
                <dd>{latest.prompt_version}</dd>
              </div>
              <div>
                <dt>Pass rate</dt>
                <dd>
                  {String(
                    latest.aggregate_metrics?.pass_rate ?? "not recorded",
                  )}
                </dd>
              </div>
              <div>
                <dt>Run time</dt>
                <dd>
                  {latest.completed_at && latest.started_at
                    ? `${Math.max(
                        0,
                        Date.parse(latest.completed_at) -
                          Date.parse(latest.started_at),
                      )} ms`
                    : "not recorded"}
                </dd>
              </div>
            </dl>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <pre className="pre-panel">
                {JSON.stringify(latest.model_metadata, null, 2)}
              </pre>
              <pre className="pre-panel">
                {JSON.stringify(latest.retrieval_configuration, null, 2)}
              </pre>
            </div>
          </section>
        )}
        <div className="table-wrap">
          <table className="data-table">
            <caption>Evaluation run comparison</caption>
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Suites</th>
                <th>Pass rate</th>
                <th>Dataset</th>
                <th>Prompt</th>
                <th>Created</th>
                <th>Report</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td>{run.name}</td>
                  <td>
                    <span className="status-label">{run.status}</span>
                  </td>
                  <td>{run.suite_names.join(", ")}</td>
                  <td>
                    {String(run.aggregate_metrics?.pass_rate ?? "not recorded")}
                  </td>
                  <td>{run.dataset_version}</td>
                  <td>{run.prompt_version}</td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                  <td>
                    {String(
                      run.environment_metadata.report_path ??
                        "Stored in database",
                    )}
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={8}>
                    No evaluation runs have been recorded in the database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppFrame>
  );
}
