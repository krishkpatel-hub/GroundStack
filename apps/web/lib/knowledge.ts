import { apiRequest } from "@/lib/api";

export type IngestionJob = {
  id: string;
  source_id: string | null;
  status: "queued" | "processing" | "completed" | "skipped" | "failed";
  current_stage: string;
  progress: number;
  statistics: Record<string, unknown>;
  error: {
    category?: string;
    message?: string;
    details?: Record<string, unknown>;
  } | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type DocumentItem = {
  id: string;
  source_id: string;
  source_type: string;
  display_name: string;
  source_status: string;
  version: number;
  title: string;
  mime_type: string;
  content_checksum: string;
  chunk_count: number;
  ingested_at: string;
};

export type DocumentChunk = {
  id: string;
  document_id: string;
  position: number;
  heading_path: string[];
  content: string;
  token_count: number;
  chunk_checksum: string;
  embedding_model: string;
  created_at: string;
};

export type Page<T> = {
  total: number;
  limit: number;
  offset: number;
  items: T[];
};

export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024;
export const ACCEPTED_FILE_EXTENSIONS = [
  ".md",
  ".markdown",
  ".txt",
  ".html",
  ".htm",
  ".pdf",
] as const;
export const ACCEPTED_FILE_TYPES = [
  "Markdown",
  "plain text",
  "HTML",
  "text-based PDF",
] as const;

export function documentStatusLabel(status: string) {
  if (status === "failed" || status === "deleted") return "Failed";
  if (status === "processing" || status === "queued") return "Processing";
  return "Ready";
}

export function documentStatusClass(status: string) {
  if (status === "failed" || status === "deleted")
    return "status-label status-danger";
  if (status === "processing" || status === "queued")
    return "status-label status-warning";
  return "status-label status-success";
}

export function validateKnowledgeFile(file: File): string | null {
  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return `${file.name} is larger than the 10 MB upload limit.`;
  }
  const lowerName = file.name.toLowerCase();
  const accepted = ACCEPTED_FILE_EXTENSIONS.some((extension) =>
    lowerName.endsWith(extension),
  );
  if (!accepted) {
    return `${file.name} is not a supported document type. Use Markdown, plain text, HTML, or text-based PDF.`;
  }
  return null;
}

export async function uploadKnowledgeFile(
  file: File,
): Promise<{ job_id: string; status: string }> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest("/api/v1/ingestions/files", { method: "POST", body });
}

export async function submitKnowledgeUrl(
  url: string,
): Promise<{ job_id: string; status: string }> {
  return apiRequest(
    "/api/v1/ingestions/url",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    },
    "URL ingestion failed",
  );
}

export async function fetchIngestionJob(jobId: string): Promise<IngestionJob> {
  return apiRequest(
    `/api/v1/ingestions/${jobId}`,
    undefined,
    "Ingestion job load failed",
  );
}

export async function fetchDocuments(
  limit = 20,
  offset = 0,
): Promise<Page<DocumentItem>> {
  return apiRequest(
    `/api/v1/documents?limit=${limit}&offset=${offset}`,
    undefined,
    "Document load failed",
  );
}

export async function fetchDocumentChunks(
  documentId: string,
  limit = 10,
  offset = 0,
): Promise<Page<DocumentChunk>> {
  return apiRequest(
    `/api/v1/documents/${documentId}/chunks?limit=${limit}&offset=${offset}`,
    undefined,
    "Document passages failed",
  );
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiRequest(
    `/api/v1/documents/${documentId}`,
    { method: "DELETE" },
    "Document deletion failed",
  );
}
