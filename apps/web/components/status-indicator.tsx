"use client";

import { AlertTriangle, CheckCircle2, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchSystemStatus, type SystemStatus } from "@/lib/status";

type StatusState =
  | { kind: "loading" }
  | { kind: "success"; status: SystemStatus }
  | { kind: "error"; message: string };

export function StatusIndicator() {
  const [state, setState] = useState<StatusState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    async function loadStatus() {
      try {
        const status = await fetchSystemStatus(controller.signal);
        setState({ kind: "success", status });
      } catch (error) {
        if (!controller.signal.aborted) {
          setState({
            kind: "error",
            message:
              error instanceof Error ? error.message : "Status check failed",
          });
        }
      }
    }

    void loadStatus();
    const interval = window.setInterval(loadStatus, 15000);

    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <div className="space-y-2" aria-live="polite">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
          Checking connection
        </div>
        <p className="text-xs leading-5 text-[var(--graphite)]">
          Waiting for API status.
        </p>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="space-y-2" aria-live="polite">
        <span className="status-label status-danger">
          <AlertTriangle className="h-4 w-4" aria-hidden />
          API unavailable
        </span>
        <p className="text-xs leading-5 text-[var(--graphite)]">
          {state.message}
        </p>
      </div>
    );
  }

  const databaseOnline = state.status.database.connected;

  return (
    <div className="space-y-2" aria-live="polite">
      <span className="status-label status-success">
        <CheckCircle2 className="h-4 w-4" aria-hidden />
        API connected
      </span>
      <div className="space-y-1 text-xs leading-5 text-[var(--graphite)]">
        <div>Database: {databaseOnline ? "Connected" : "Unavailable"}</div>
        {state.status.retrieval && (
          <div>
            Searchable chunks: {state.status.retrieval.searchable_chunks}
          </div>
        )}
        {state.status.retrieval && (
          <div>
            Reranking:{" "}
            {state.status.retrieval.reranking_enabled ? "Enabled" : "Disabled"}
          </div>
        )}
        {state.status.llm && (
          <div>
            LLM: {state.status.llm.provider}/{state.status.llm.model}{" "}
            {state.status.llm.model_available ? "ready" : "unavailable"}
          </div>
        )}
        {state.status.llm && (
          <div>
            Model: {state.status.llm.model_variant}
            {state.status.llm.adapter_name
              ? ` (${state.status.llm.adapter_name} ${state.status.llm.adapter_version ?? ""})`
              : ""}
          </div>
        )}
        {state.status.llm && (
          <div>Promotion: {state.status.llm.promotion_status}</div>
        )}
        <div>Environment: {state.status.environment}</div>
      </div>
    </div>
  );
}
