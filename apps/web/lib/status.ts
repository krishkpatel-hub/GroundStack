import { apiRequest } from "@/lib/api";

export type SystemStatus = {
  application: string;
  environment: string;
  database: {
    connected: boolean;
    detail: string;
  };
  retrieval?: {
    algorithm_version: string;
    reranking_enabled: boolean;
    vector_index_available: boolean;
    text_search_index_available: boolean;
    searchable_sources: number;
    searchable_chunks: number;
  };
  llm?: {
    provider: string;
    model: string;
    reachable: boolean;
    model_available: boolean;
    loaded: boolean | null;
    detail: string;
    model_variant: string;
    adapter_name: string | null;
    adapter_version: string | null;
    dataset_version: string | null;
    model_manifest_checksum: string | null;
    evaluation_status: string;
    promotion_status: string;
  };
};

export async function fetchSystemStatus(
  signal?: AbortSignal,
): Promise<SystemStatus> {
  return apiRequest("/api/v1/system/status", { signal }, "Status check failed");
}
