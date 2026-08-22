"use client";

import { ChevronDown, ChevronRight, FileUp, RefreshCw } from "lucide-react";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";

import { AppFrame } from "@/components/app-frame";
import {
  fetchDocumentChunks,
  fetchDocuments,
  fetchIngestionJob,
  submitKnowledgeUrl,
  uploadKnowledgeFile,
  type DocumentChunk,
  type DocumentItem,
  type IngestionJob,
  type Page,
} from "@/lib/knowledge";

const pageSize = 3;

function createOptimisticJob(job: {
  job_id: string;
  status: string;
}): IngestionJob {
  const timestamp = new Date().toISOString();
  return {
    id: job.job_id,
    status: job.status as IngestionJob["status"],
    source_id: null,
    current_stage: "queued",
    progress: 0,
    statistics: {},
    error: null,
    created_at: timestamp,
    updated_at: timestamp,
    started_at: null,
    completed_at: null,
  };
}

function statusClass(status: string) {
  if (status === "failed") return "status-label status-danger";
  if (status === "processing" || status === "queued")
    return "status-label status-warning";
  return "status-label status-success";
}

export function KnowledgeBase({
  mode = "admin",
}: {
  mode?: "admin" | "activity";
}) {
  const [documents, setDocuments] = useState<Page<DocumentItem> | null>(null);
  const [offset, setOffset] = useState(0);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [chunks, setChunks] = useState<Record<string, Page<DocumentChunk>>>({});
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [dragActive, setDragActive] = useState(false);

  const loadDocuments = useCallback(
    async (nextOffset = offset) => {
      setLoadingDocs(true);
      try {
        setDocuments(await fetchDocuments(pageSize, nextOffset));
        setError(null);
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Could not load documents",
        );
      } finally {
        setLoadingDocs(false);
      }
    },
    [offset],
  );

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadDocuments(offset), 0);
    return () => window.clearTimeout(timeout);
  }, [loadDocuments, offset]);

  useEffect(() => {
    if (!jobs.some((job) => ["queued", "processing"].includes(job.status)))
      return;
    const interval = window.setInterval(async () => {
      const refreshed = await Promise.all(
        jobs.map((job) => fetchIngestionJob(job.id)),
      );
      setJobs(refreshed);
      if (
        refreshed.some((job) => ["completed", "skipped"].includes(job.status))
      ) {
        void loadDocuments(0);
      }
    }, 1600);
    return () => window.clearInterval(interval);
  }, [jobs, loadDocuments]);

  async function acceptFiles(files: FileList | File[]) {
    setError(null);
    try {
      const accepted = await Promise.all(
        Array.from(files).map((file) => uploadKnowledgeFile(file)),
      );
      setJobs((current) => [...accepted.map(createOptimisticJob), ...current]);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : "Upload failed",
      );
    }
  }

  async function submitUrl() {
    if (!url.trim()) return;
    setError(null);
    try {
      const job = await submitKnowledgeUrl(url.trim());
      setJobs((current) => [createOptimisticJob(job), ...current]);
      setUrl("");
    } catch (urlError) {
      setError(
        urlError instanceof Error ? urlError.message : "URL ingestion failed",
      );
    }
  }

  async function toggleDocument(documentId: string) {
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

  const pageLabel = useMemo(() => {
    if (!documents) return "0-0";
    return `${documents.total === 0 ? 0 : documents.offset + 1}-${Math.min(
      documents.offset + documents.items.length,
      documents.total,
    )}`;
  }, [documents]);

  return (
    <AppFrame
      title={
        mode === "activity"
          ? "Ingestion activity"
          : "Knowledge-base administration"
      }
      description={
        mode === "activity"
          ? "Track ingestion jobs, recovery states, and document processing progress."
          : "Ingest technical sources, monitor processing, and inspect stored document versions and chunks."
      }
      actions={
        <button
          className="button"
          type="button"
          onClick={() => void loadDocuments(offset)}
        >
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh
        </button>
      }
    >
      <div className="space-y-8">
        {mode === "admin" && (
          <section aria-labelledby="ingestion-heading" className="space-y-4">
            <div>
              <h2 id="ingestion-heading" className="section-title">
                Add knowledge
              </h2>
              <p className="mt-1 text-sm leading-6 text-[var(--graphite)]">
                Supported formats: Markdown, plain text, HTML, and text-based
                PDF. URL ingestion accepts only allowlisted public documentation
                pages.
              </p>
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,420px)]">
              <div
                className={`upload-boundary p-4 ${dragActive ? "border-[var(--accent)]" : ""}`}
                onDragEnter={() => setDragActive(true)}
                onDragLeave={() => setDragActive(false)}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragActive(false);
                  void acceptFiles(event.dataTransfer.files);
                }}
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="font-semibold">Upload files</h3>
                    <p className="mt-1 text-sm leading-6 text-[var(--graphite)]">
                      Drop files here or choose them from disk.
                    </p>
                  </div>
                  <label className="button button-primary cursor-pointer">
                    <FileUp className="h-4 w-4" aria-hidden />
                    Choose files
                    <input
                      type="file"
                      multiple
                      accept=".md,.markdown,.txt,.html,.htm,.pdf,text/markdown,text/plain,text/html,application/pdf"
                      className="sr-only"
                      onChange={(event) =>
                        event.target.files &&
                        void acceptFiles(event.target.files)
                      }
                    />
                  </label>
                </div>
              </div>

              <div>
                <label htmlFor="knowledge-url" className="label">
                  Public documentation URL
                </label>
                <div className="flex gap-2 max-sm:flex-col">
                  <input
                    id="knowledge-url"
                    value={url}
                    onChange={(event) => setUrl(event.target.value)}
                    placeholder="https://docs.example.com/page"
                    className="field min-w-0"
                  />
                  <button
                    className="button"
                    type="button"
                    onClick={() => void submitUrl()}
                  >
                    Submit URL
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        <section aria-labelledby="activity-heading" className="divider pt-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="activity-heading" className="section-title">
              Ingestion activity
            </h2>
            <span className="text-sm text-[var(--graphite)]" aria-live="polite">
              {jobs.length === 0
                ? "No active jobs"
                : `${jobs.length} recent job${jobs.length === 1 ? "" : "s"}`}
            </span>
          </div>

          {error && (
            <div className="inline-alert mt-4" role="alert">
              {error}
            </div>
          )}

          {jobs.length > 0 && (
            <div className="mt-4 space-y-3" aria-live="polite">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="border-t border-[var(--border)] pt-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <div className="font-semibold">{job.current_stage}</div>
                      <div className="mono mt-1 truncate text-xs text-[var(--graphite)]">
                        {job.id}
                      </div>
                    </div>
                    <span className={statusClass(job.status)}>
                      {job.status}
                    </span>
                  </div>
                  <progress
                    className="mt-3 h-2 w-full"
                    max={100}
                    value={job.progress}
                  >
                    {job.progress}%
                  </progress>
                  {job.error?.message && (
                    <p className="mt-2 text-sm leading-6 text-[var(--danger)]">
                      {job.error.message}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        <section aria-labelledby="documents-heading" className="divider pt-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 id="documents-heading" className="section-title">
                Document inventory
              </h2>
              <p className="mt-1 text-sm text-[var(--graphite)]">
                {documents
                  ? `${pageLabel} of ${documents.total}`
                  : "Loading documents"}
              </p>
            </div>
            {loadingDocs && (
              <span className="status-label status-warning">Loading</span>
            )}
          </div>

          {!loadingDocs && documents?.items.length === 0 && (
            <p className="mt-6 max-w-xl text-sm leading-6 text-[var(--graphite)]">
              No documents have been ingested yet. Upload a supported file or
              submit an allowlisted documentation URL to begin.
            </p>
          )}

          {documents && documents.items.length > 0 && (
            <>
              <div className="desktop-inventory table-wrap mt-4">
                <table className="data-table">
                  <caption className="sr-only">
                    Ingested document versions
                  </caption>
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Source</th>
                      <th>Version</th>
                      <th>Status</th>
                      <th>Chunks</th>
                      <th>Ingested</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.items.map((document) => {
                      const isExpanded = expanded === document.id;
                      return (
                        <Fragment key={document.id}>
                          <tr>
                            <td>
                              <div className="max-w-[280px] break-words font-semibold">
                                {document.title}
                              </div>
                              <div className="mono mt-1 truncate text-xs text-[var(--graphite)]">
                                {document.content_checksum}
                              </div>
                            </td>
                            <td>
                              <div>{document.source_type}</div>
                              <div className="mt-1 max-w-[180px] truncate text-xs text-[var(--graphite)]">
                                {document.display_name}
                              </div>
                            </td>
                            <td className="mono">v{document.version}</td>
                            <td>
                              <span className="status-label status-success">
                                {document.source_status}
                              </span>
                            </td>
                            <td>{document.chunk_count}</td>
                            <td>
                              {new Date(document.ingested_at).toLocaleString()}
                            </td>
                            <td>
                              <button
                                className="button min-h-9 px-2 py-1"
                                type="button"
                                aria-expanded={isExpanded}
                                onClick={() => void toggleDocument(document.id)}
                              >
                                {isExpanded ? (
                                  <ChevronDown
                                    className="h-4 w-4"
                                    aria-hidden
                                  />
                                ) : (
                                  <ChevronRight
                                    className="h-4 w-4"
                                    aria-hidden
                                  />
                                )}
                                Chunks
                              </button>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr>
                              <td colSpan={7}>
                                <div className="space-y-3 py-2">
                                  {(chunks[document.id]?.items ?? []).map(
                                    (chunk) => (
                                      <section
                                        key={chunk.id}
                                        className="border-l-2 border-[var(--border-strong)] pl-3"
                                      >
                                        <div className="mono text-xs leading-5 text-[var(--graphite)]">
                                          #{chunk.position} -{" "}
                                          <span className="break-words">
                                            {chunk.heading_path.join(" / ") ||
                                              "Root"}
                                          </span>{" "}
                                          - {chunk.token_count} tokens
                                        </div>
                                        <p className="mt-1 line-clamp-5 whitespace-pre-wrap text-sm leading-6">
                                          {chunk.content}
                                        </p>
                                      </section>
                                    ),
                                  )}
                                  {chunks[document.id]?.items.length === 0 && (
                                    <p className="text-sm text-[var(--graphite)]">
                                      Loading chunks...
                                    </p>
                                  )}
                                </div>
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="mobile-inventory mt-4">
                {documents.items.map((document) => {
                  const isExpanded = expanded === document.id;
                  return (
                    <section key={document.id} className="document-row">
                      <div>
                        <h3 className="break-words font-semibold">
                          {document.title}
                        </h3>
                        <div className="mono mt-1 break-all text-xs text-[var(--graphite)]">
                          {document.content_checksum}
                        </div>
                      </div>
                      <dl className="document-facts">
                        <div>
                          <dt>Source</dt>
                          <dd>
                            {document.source_type}, {document.display_name}
                          </dd>
                        </div>
                        <div>
                          <dt>Version</dt>
                          <dd>v{document.version}</dd>
                        </div>
                        <div>
                          <dt>Status</dt>
                          <dd>
                            <span className="status-label status-success">
                              {document.source_status}
                            </span>
                          </dd>
                        </div>
                        <div>
                          <dt>Chunks</dt>
                          <dd>{document.chunk_count}</dd>
                        </div>
                        <div>
                          <dt>Ingested</dt>
                          <dd>
                            {new Date(document.ingested_at).toLocaleString()}
                          </dd>
                        </div>
                      </dl>
                      <button
                        className="button min-h-9 w-full px-2 py-1"
                        type="button"
                        aria-expanded={isExpanded}
                        onClick={() => void toggleDocument(document.id)}
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" aria-hidden />
                        ) : (
                          <ChevronRight className="h-4 w-4" aria-hidden />
                        )}
                        Chunks
                      </button>
                      {isExpanded && (
                        <div className="space-y-3">
                          {(chunks[document.id]?.items ?? []).map((chunk) => (
                            <section
                              key={chunk.id}
                              className="border-l-2 border-[var(--border-strong)] pl-3"
                            >
                              <div className="mono text-xs leading-5 text-[var(--graphite)]">
                                #{chunk.position} -{" "}
                                <span className="break-words">
                                  {chunk.heading_path.join(" / ") || "Root"}
                                </span>{" "}
                                - {chunk.token_count} tokens
                              </div>
                              <p className="mt-1 line-clamp-5 whitespace-pre-wrap text-sm leading-6">
                                {chunk.content}
                              </p>
                            </section>
                          ))}
                          {chunks[document.id]?.items.length === 0 && (
                            <p className="text-sm text-[var(--graphite)]">
                              Loading chunks...
                            </p>
                          )}
                        </div>
                      )}
                    </section>
                  );
                })}
              </div>
            </>
          )}

          <div className="mt-4 flex flex-wrap justify-between gap-3">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - pageSize))}
              className="button"
              type="button"
            >
              Previous
            </button>
            <button
              disabled={!documents || offset + pageSize >= documents.total}
              onClick={() => setOffset(offset + pageSize)}
              className="button"
              type="button"
            >
              Next
            </button>
          </div>
        </section>
      </div>
    </AppFrame>
  );
}
