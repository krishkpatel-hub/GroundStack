"use client";

import {
  CheckCircle2,
  FileText,
  LoaderCircle,
  MessageSquare,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchDocuments } from "@/lib/knowledge";

type KnowledgeState =
  | { kind: "loading" }
  | { kind: "ready"; count: number }
  | { kind: "error"; message: string };

export function WorkspaceNav() {
  const pathname = usePathname();
  const active = pathname.startsWith("/knowledge") ? "documents" : "ask";

  return (
    <div className="workspace-toolbar" aria-label="Workspace navigation">
      <div
        className="workspace-tabs"
        role="tablist"
        aria-label="Workspace views"
        onKeyDown={(event) => {
          if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
          event.preventDefault();
          const tabs = Array.from(
            event.currentTarget.querySelectorAll<HTMLAnchorElement>(
              "[role='tab']",
            ),
          );
          const current = tabs.indexOf(
            document.activeElement as HTMLAnchorElement,
          );
          const direction = event.key === "ArrowRight" ? 1 : -1;
          const next = tabs[(current + direction + tabs.length) % tabs.length];
          next?.focus();
          next?.click();
        }}
      >
        <WorkspaceTab
          href="/ask"
          active={active === "ask"}
          label="Ask"
          icon="ask"
        />
        <WorkspaceTab
          href="/knowledge"
          active={active === "documents"}
          label="Documents"
          icon="documents"
        />
      </div>
      <KnowledgeBaseStatus />
    </div>
  );
}

function WorkspaceTab({
  href,
  active,
  label,
  icon,
}: {
  href: string;
  active: boolean;
  label: string;
  icon: "ask" | "documents";
}) {
  const Icon = icon === "ask" ? MessageSquare : FileText;
  return (
    <Link
      aria-current={active ? "page" : undefined}
      aria-selected={active}
      className={`workspace-tab ${active ? "workspace-tab-active" : ""}`}
      href={href}
      role="tab"
      tabIndex={active ? 0 : -1}
    >
      <Icon className="h-4 w-4" aria-hidden />
      {label}
    </Link>
  );
}

function KnowledgeBaseStatus() {
  const [state, setState] = useState<KnowledgeState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchDocuments(100, 0)
      .then((page) => {
        if (!controller.signal.aborted) {
          setState({ kind: "ready", count: page.total });
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setState({
            kind: "error",
            message:
              error instanceof Error ? error.message : "Service unavailable",
          });
        }
      });
    return () => controller.abort();
  }, []);

  if (state.kind === "loading") {
    return (
      <span className="status-label" aria-live="polite">
        <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
        Checking knowledge base
      </span>
    );
  }

  if (state.kind === "error") return null;

  return (
    <span
      className={`status-label ${state.count > 0 ? "status-success" : "status-warning"}`}
      aria-live="polite"
    >
      <CheckCircle2 className="h-4 w-4" aria-hidden />
      {state.count === 0
        ? "No documents"
        : `${state.count} document${state.count === 1 ? "" : "s"} ready`}
    </span>
  );
}
