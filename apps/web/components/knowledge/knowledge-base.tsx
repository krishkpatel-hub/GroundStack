"use client";

import {
  ChevronDown,
  ChevronRight,
  FileUp,
  RefreshCw,
  Trash2,
} from "lucide-react";
import {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ApiConnectionAlert } from "@/components/api-connection-alert";
import { AppFrame } from "@/components/app-frame";
import { WorkspaceNav } from "@/components/workspace-nav";
import { friendlyApiError } from "@/lib/api";
import {
  ACCEPTED_FILE_TYPES,
  deleteDocument,
  documentStatusClass,
  documentStatusLabel,
  fetchDocumentChunks,
  fetchDocuments,
  fetchIngestionJob,
  submitKnowledgeUrl,
  uploadKnowledgeFile,
  validateKnowledgeFile,
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
  const [selectedFileNames, setSelectedFileNames] = useState<string[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);
  const [fileSubmitting, setFileSubmitting] = useState(false);
  const [urlSubmitting, setUrlSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const uploadInFlightRef = useRef(false);
  const urlInFlightRef = useRef(false);
  const deleteInFlightRef = useRef(false);
  const retrySourcesRef = useRef(new Map<string, File | string>());
  const deleteDialogRef = useRef<HTMLElement | null>(null);
  const deleteTriggerRef = useRef<HTMLButtonElement | null>(null);

  const loadDocuments = useCallback(
    async (nextOffset = offset) => {
      setLoadingDocs(true);
      setError(null);
      try {
        setDocuments(await fetchDocuments(pageSize, nextOffset));
      } catch (loadError) {
        setError(
          friendlyApiError(loadError, "Could not load documents").message,
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
      try {
        const refreshed = await Promise.all(
          jobs.map((job) => fetchIngestionJob(job.id)),
        );
        setJobs((current) =>
          current.map(
            (job) => refreshed.find((item) => item.id === job.id) ?? job,
          ),
        );
        refreshed
          .filter((job) => ["completed", "skipped"].includes(job.status))
          .forEach((job) => retrySourcesRef.current.delete(job.id));
        if (
          refreshed.some((job) => ["completed", "skipped"].includes(job.status))
        ) {
          void loadDocuments(0);
        }
      } catch (pollError) {
        setError(
          friendlyApiError(pollError, "Could not refresh processing status")
            .message,
        );
      }
    }, 1600);
    return () => window.clearInterval(interval);
  }, [jobs, loadDocuments]);

  useEffect(() => {
    if (!deleteTarget) return;
    deleteDialogRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setDeleteTarget(null);
        window.requestAnimationFrame(() => deleteTriggerRef.current?.focus());
        return;
      }
      if (event.key !== "Tab" || !deleteDialogRef.current) return;
      const focusable = Array.from(
        deleteDialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [deleteTarget]);

  async function acceptFiles(files: FileList | File[]) {
    if (uploadInFlightRef.current) return;
    setError(null);
    const fileList = Array.from(files);
    if (fileList.length === 0) return;
    setSelectedFileNames(fileList.map((file) => file.name));
    const validationError = fileList
      .map(validateKnowledgeFile)
      .find((message): message is string => Boolean(message));
    if (validationError) {
      setError(validationError);
      return;
    }
    setFileSubmitting(true);
    uploadInFlightRef.current = true;
    try {
      const accepted = await Promise.allSettled(
        fileList.map((file) => uploadKnowledgeFile(file)),
      );
      const newJobs: IngestionJob[] = [];
      accepted.forEach((result, index) => {
        if (result.status === "fulfilled") {
          retrySourcesRef.current.set(result.value.job_id, fileList[index]);
          newJobs.push(createOptimisticJob(result.value));
        } else {
          setError(
            friendlyApiError(
              result.reason,
              "Upload failed. Choose the file again to retry.",
            ).message,
          );
        }
      });
      setJobs((current) => [...newJobs, ...current]);
    } catch (uploadError) {
      setError(friendlyApiError(uploadError, "Upload failed").message);
    } finally {
      uploadInFlightRef.current = false;
      setFileSubmitting(false);
    }
  }

  async function submitUrl() {
    if (!url.trim() || urlInFlightRef.current) return;
    urlInFlightRef.current = true;
    setError(null);
    setUrlSubmitting(true);
    try {
      const job = await submitKnowledgeUrl(url.trim());
      retrySourcesRef.current.set(job.job_id, url.trim());
      setJobs((current) => [createOptimisticJob(job), ...current]);
      setUrl("");
    } catch (urlError) {
      setError(friendlyApiError(urlError, "URL ingestion failed").message);
    } finally {
      urlInFlightRef.current = false;
      setUrlSubmitting(false);
    }
  }

  async function confirmDeleteDocument() {
    if (!deleteTarget || deleteInFlightRef.current) return;
    deleteInFlightRef.current = true;
    setDeleting(true);
    setError(null);
    try {
      await deleteDocument(deleteTarget.id);
      setDeleteTarget(null);
      setExpanded((current) => (current === deleteTarget.id ? null : current));
      setChunks((current) => {
        const next = { ...current };
        delete next[deleteTarget.id];
        return next;
      });
      const nextOffset =
        documents?.items.length === 1 ? Math.max(0, offset - pageSize) : offset;
      setOffset(nextOffset);
      await loadDocuments(nextOffset);
    } catch (deleteError) {
      setError(
        friendlyApiError(deleteError, "Document deletion failed").message,
      );
    } finally {
      deleteInFlightRef.current = false;
      setDeleting(false);
    }
  }

  async function retryJob(jobId: string) {
    const source = retrySourcesRef.current.get(jobId);
    if (!source || uploadInFlightRef.current || urlInFlightRef.current) return;
    uploadInFlightRef.current = true;
    setFileSubmitting(true);
    setError(null);
    try {
      const accepted =
        typeof source === "string"
          ? await submitKnowledgeUrl(source)
          : await uploadKnowledgeFile(source);
      retrySourcesRef.current.delete(jobId);
      retrySourcesRef.current.set(accepted.job_id, source);
      setJobs((current) =>
        current.map((job) =>
          job.id === jobId ? createOptimisticJob(accepted) : job,
        ),
      );
    } catch (retryError) {
      setError(
        friendlyApiError(retryError, "Could not retry processing. Try again.")
          .message,
      );
    } finally {
      uploadInFlightRef.current = false;
      setFileSubmitting(false);
    }
  }

  async function toggleDocument(documentId: string) {
    const next = expanded === documentId ? null : documentId;
    setExpanded(next);
    if (next && !chunks[next]) {
      setError(null);
      setChunks((current) => ({
        ...current,
        [next]: { total: 0, limit: 10, offset: 0, items: [] },
      }));
      try {
        const page = await fetchDocumentChunks(next, 10, 0);
        setChunks((current) => ({ ...current, [next]: page }));
      } catch (chunkError) {
        setChunks((current) => {
          const nextChunks = { ...current };
          delete nextChunks[next];
          return nextChunks;
        });
        setExpanded((current) => (current === next ? null : current));
        setError(
          friendlyApiError(chunkError, "Could not load source excerpts")
            .message,
        );
      }
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
      title={mode === "activity" ? "Ingestion activity" : "Workspace"}
      description={
        mode === "activity"
          ? "Track ingestion jobs, recovery states, and document processing progress."
          : "Add and manage the approved documents GroundStack can use as evidence."
      }
      requireAdmin
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
      {mode === "admin" && <WorkspaceNav documentCount={documents?.total} />}
      <div className="space-y-8">
        {mode === "admin" && (
          <section aria-labelledby="ingestion-heading" className="space-y-4">
            <div className="demo-workspace-note">
              <div>
                <p className="eyebrow">Organization knowledge base</p>
                <h2>Start with approved documentation</h2>
                <p>
                  Upload only material your organization is authorized to
                  process. GroundStack uses Ready documents as evidence and
                  refuses questions the knowledge base cannot support.
                </p>
              </div>
            </div>
            <div>
              <h2 id="ingestion-heading" className="section-title">
                Knowledge base
              </h2>
              <p className="mt-1 text-sm leading-6 text-[var(--graphite)]">
                Accepted file types: {ACCEPTED_FILE_TYPES.join(", ")}. Maximum
                file size: 10 MB.
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
                    <h3 className="font-semibold">Upload documents</h3>
                    <p className="mt-1 text-sm leading-6 text-[var(--graphite)]">
                      Drop files here or choose them from disk.
                    </p>
                    {selectedFileNames.length > 0 && (
                      <p className="mt-2 text-sm leading-6 text-[var(--graphite-strong)]">
                        Selected: {selectedFileNames.join(", ")}
                      </p>
                    )}
                  </div>
                  <label
                    className={`button button-primary cursor-pointer ${fileSubmitting ? "opacity-70" : ""}`}
                    aria-disabled={fileSubmitting}
                  >
                    <FileUp className="h-4 w-4" aria-hidden />
                    {fileSubmitting ? "Uploading" : "Choose files"}
                    <input
                      type="file"
                      multiple
                      accept=".md,.markdown,.txt,.html,.htm,.pdf,text/markdown,text/plain,text/html,application/pdf"
                      className="sr-only"
                      disabled={fileSubmitting}
                      onChange={(event) => {
                        const files = Array.from(
                          event.currentTarget.files ?? [],
                        );
                        event.currentTarget.value = "";
                        if (files.length > 0) void acceptFiles(files);
                      }}
                    />
                  </label>
                </div>
              </div>

              <div>
                <label htmlFor="knowledge-url" className="label">
                  Documentation URL
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
                    disabled={urlSubmitting || !url.trim()}
                    onClick={() => void submitUrl()}
                  >
                    {urlSubmitting ? "Submitting" : "Submit URL"}
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        <section aria-labelledby="activity-heading" className="divider pt-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="activity-heading" className="section-title">
              Processing status
            </h2>
            <span className="text-sm text-[var(--graphite)]" aria-live="polite">
              {jobs.length === 0
                ? "No active jobs"
                : `${jobs.length} recent job${jobs.length === 1 ? "" : "s"}`}
            </span>
          </div>

          {error && (
            <div className="mt-4">
              <ApiConnectionAlert
                message={error}
                onRetry={() => void loadDocuments(offset)}
              />
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
                      <div className="font-semibold">
                        {documentStatusLabel(job.status)}
                      </div>
                      <div className="mono mt-1 truncate text-xs text-[var(--graphite)]">
                        {job.id}
                      </div>
                    </div>
                    <span className={documentStatusClass(job.status)}>
                      {documentStatusLabel(job.status)}
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
                  {job.status === "failed" && (
                    <button
                      className="button mt-2"
                      type="button"
                      disabled={fileSubmitting || urlSubmitting}
                      onClick={() => void retryJob(job.id)}
                    >
                      <RefreshCw className="h-4 w-4" aria-hidden /> Retry
                      processing
                    </button>
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
                Documents
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
              No documents yet. Upload a supported file or submit an allowed
              documentation URL. Wait for Ready before asking a question.
            </p>
          )}

          {documents && documents.items.length > 0 && (
            <>
              <div className="desktop-inventory table-wrap mt-4">
                <table className="data-table">
                  <caption className="sr-only">
                    Approved technical-support documents
                  </caption>
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Source</th>
                      <th>Version</th>
                      <th>Status</th>
                      <th>Chunks</th>
                      <th>Added</th>
                      <th>Details</th>
                      {mode === "admin" && <th>Delete</th>}
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
                            </td>
                            <td>
                              <div>{document.source_type}</div>
                              <div className="mt-1 max-w-[180px] truncate text-xs text-[var(--graphite)]">
                                {document.display_name}
                              </div>
                            </td>
                            <td className="mono">v{document.version}</td>
                            <td>
                              <span
                                className={documentStatusClass(
                                  document.source_status,
                                )}
                              >
                                {documentStatusLabel(document.source_status)}
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
                                Source excerpts
                              </button>
                            </td>
                            {mode === "admin" && (
                              <td>
                                <button
                                  className="button button-danger min-h-9 px-2 py-1"
                                  type="button"
                                  onClick={(event) => {
                                    deleteTriggerRef.current =
                                      event.currentTarget;
                                    setDeleteTarget(document);
                                  }}
                                >
                                  <Trash2 className="h-4 w-4" aria-hidden />
                                  Delete
                                </button>
                              </td>
                            )}
                          </tr>
                          {isExpanded && (
                            <tr>
                              <td colSpan={mode === "admin" ? 8 : 7}>
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
                                        </div>
                                        <p className="mt-1 whitespace-pre-wrap text-sm leading-6">
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
                            <span
                              className={documentStatusClass(
                                document.source_status,
                              )}
                            >
                              {documentStatusLabel(document.source_status)}
                            </span>
                          </dd>
                        </div>
                        <div>
                          <dt>Chunks</dt>
                          <dd>{document.chunk_count}</dd>
                        </div>
                        <div>
                          <dt>Added</dt>
                          <dd>
                            {new Date(document.ingested_at).toLocaleString()}
                          </dd>
                        </div>
                      </dl>
                      <div className="document-actions">
                        <button
                          className="button min-h-9 px-2 py-1"
                          type="button"
                          aria-expanded={isExpanded}
                          onClick={() => void toggleDocument(document.id)}
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" aria-hidden />
                          ) : (
                            <ChevronRight className="h-4 w-4" aria-hidden />
                          )}
                          Source excerpts
                        </button>
                        {mode === "admin" && (
                          <button
                            className="button button-danger min-h-9 px-2 py-1"
                            type="button"
                            onClick={(event) => {
                              deleteTriggerRef.current = event.currentTarget;
                              setDeleteTarget(document);
                            }}
                          >
                            <Trash2 className="h-4 w-4" aria-hidden />
                            Delete
                          </button>
                        )}
                      </div>
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
                              </div>
                              <p className="mt-1 whitespace-pre-wrap text-sm leading-6">
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

      {deleteTarget && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => {
            setDeleteTarget(null);
            window.requestAnimationFrame(() =>
              deleteTriggerRef.current?.focus(),
            );
          }}
        >
          <section
            ref={deleteDialogRef}
            className="modal-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-document-title"
            tabIndex={-1}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="delete-document-title" className="section-title">
              Delete document?
            </h2>
            <p className="mt-3 text-sm leading-6 text-[var(--graphite)]">
              This removes <strong>{deleteTarget.title}</strong> and its stored
              source chunks from future answers. Existing conversation records
              are not edited.
            </p>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button
                className="button"
                type="button"
                onClick={() => {
                  setDeleteTarget(null);
                  window.requestAnimationFrame(() =>
                    deleteTriggerRef.current?.focus(),
                  );
                }}
              >
                Cancel
              </button>
              <button
                className="button button-danger"
                type="button"
                disabled={deleting}
                onClick={() => void confirmDeleteDocument()}
              >
                {deleting ? "Deleting" : "Delete document"}
              </button>
            </div>
          </section>
        </div>
      )}
    </AppFrame>
  );
}
