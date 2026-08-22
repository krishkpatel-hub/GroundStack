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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadKnowledgeFile(
  file: File,
): Promise<{ job_id: string; status: string }> {
  const body = new FormData();
  body.append("file", file);
  return request("/api/v1/ingestions/files", { method: "POST", body });
}

export async function submitKnowledgeUrl(
  url: string,
): Promise<{ job_id: string; status: string }> {
  return request("/api/v1/ingestions/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function fetchIngestionJob(jobId: string): Promise<IngestionJob> {
  return request(`/api/v1/ingestions/${jobId}`);
}

export async function fetchDocuments(
  limit = 20,
  offset = 0,
): Promise<Page<DocumentItem>> {
  return request(`/api/v1/documents?limit=${limit}&offset=${offset}`);
}

export async function fetchDocumentChunks(
  documentId: string,
  limit = 10,
  offset = 0,
): Promise<Page<DocumentChunk>> {
  return request(
    `/api/v1/documents/${documentId}/chunks?limit=${limit}&offset=${offset}`,
  );
}
