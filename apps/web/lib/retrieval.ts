const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type RetrievalFilters = {
  source_types?: string[];
  source_ids?: string[];
  document_ids?: string[];
};

export type Citation = {
  citation_id: string;
  source_id: string;
  document_id: string;
  document_version: number;
  chunk_id: string;
  title: string;
  source_display_name: string;
  source_type: string;
  source_uri: string | null;
  section_path: string | null;
  page_number: number | null;
  excerpt: string;
  final_rank: number;
};

export type RetrievalSearchResponse = {
  retrieval_run_id: string | null;
  normalized_query: string;
  result_count: number;
  evidence_found: boolean;
  reranking_applied: boolean;
  degraded_mode: {
    stage?: string;
    reason?: string;
    message?: string;
  } | null;
  applied_filters: RetrievalFilters;
  citations: Citation[];
  timings_ms: Record<string, number>;
  debug: unknown[] | null;
};

export async function searchRetrieval(
  payload: {
    query: string;
    top_k: number;
    filters: RetrievalFilters;
    include_debug?: boolean;
  },
  signal?: AbortSignal,
): Promise<RetrievalSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/retrieval/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { message?: string };
      detail?: unknown;
    } | null;
    throw new Error(
      body?.error?.message ?? `Retrieval failed with ${response.status}`,
    );
  }
  return response.json() as Promise<RetrievalSearchResponse>;
}
