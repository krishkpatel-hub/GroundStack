"use client";

import { ChevronDown, ChevronRight, RefreshCw } from "lucide-react";
import { Fragment, useCallback, useEffect, useState } from "react";

import { AppFrame } from "@/components/app-frame";
import {
  fetchDocumentChunks,
  fetchDocuments,
  type DocumentChunk,
  type DocumentItem,
  type Page,
} from "@/lib/knowledge";

export function SourceInventory() {
  const [documents, setDocuments] = useState<Page<DocumentItem> | null>(null);
  const [chunks, setChunks] = useState<Record<string, Page<DocumentChunk>>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDocuments(await fetchDocuments(20, 0));
      setError(null);
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "Source load failed",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function toggle(documentId: string) {
    const next = expanded === documentId ? null : documentId;
    setExpanded(next);
    if (next && !chunks[next]) {
      setChunks((current) => ({
        ...current,
        [next]: { total: 0, limit: 10, offset: 0, items: [] },
      }));
      const page = await fetchDocumentChunks(next, 10, 0);
      setChunks((current) => ({ ...current, [next]: page }));
    }
  }

  return (
    <AppFrame
      title="Sources and citations"
      description="Inspect the admin-managed knowledge corpus that GroundStack can cite."
      actions={
        <button className="button" type="button" onClick={() => void load()}>
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh
        </button>
      }
    >
      {loading && (
        <p className="text-sm text-[var(--graphite)]">
          Loading source inventory.
        </p>
      )}
      {error && <div className="inline-alert">{error}</div>}
      {!loading && documents?.items.length === 0 && (
        <section className="empty-chat">
          <h2 className="section-title">No documents yet</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--graphite)]">
            The knowledge base is empty. Ask an administrator to add
            documentation before expecting grounded answers.
          </p>
        </section>
      )}
      {documents && documents.items.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <caption>
              Inspectable document versions available for citation
            </caption>
            <thead>
              <tr>
                <th>Document</th>
                <th>Source</th>
                <th>Status</th>
                <th>Chunks</th>
                <th>Version</th>
                <th>Ingested</th>
                <th>Passages</th>
              </tr>
            </thead>
            <tbody>
              {documents.items.map((document) => (
                <Fragment key={document.id}>
                  <tr>
                    <td>
                      <strong>{document.title}</strong>
                      <div className="text-xs text-[var(--graphite)]">
                        {document.mime_type}
                      </div>
                    </td>
                    <td>{document.display_name}</td>
                    <td>
                      <span className="status-label status-success">
                        {document.source_status}
                      </span>
                    </td>
                    <td>{document.chunk_count}</td>
                    <td>v{document.version}</td>
                    <td>{new Date(document.ingested_at).toLocaleString()}</td>
                    <td>
                      <button
                        className="button min-h-9"
                        type="button"
                        aria-expanded={expanded === document.id}
                        onClick={() => void toggle(document.id)}
                      >
                        {expanded === document.id ? (
                          <ChevronDown className="h-4 w-4" aria-hidden />
                        ) : (
                          <ChevronRight className="h-4 w-4" aria-hidden />
                        )}
                        View
                      </button>
                    </td>
                  </tr>
                  {expanded === document.id && (
                    <tr>
                      <td colSpan={7}>
                        <div className="space-y-3 py-2">
                          {(chunks[document.id]?.items ?? []).map((chunk) => (
                            <section key={chunk.id} className="evidence-row">
                              <h3 className="text-sm font-semibold">
                                {chunk.heading_path.join(" / ") || "Root"}
                              </h3>
                              <p className="mt-1 whitespace-pre-wrap text-sm leading-6">
                                {chunk.content}
                              </p>
                            </section>
                          ))}
                          {chunks[document.id]?.items.length === 0 && (
                            <p className="text-sm text-[var(--graphite)]">
                              Loading passages.
                            </p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppFrame>
  );
}
