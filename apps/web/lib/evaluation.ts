import { apiRequest } from "@/lib/api";

export type EvaluationRun = {
  id: string;
  name: string;
  status: string;
  suite_names: string[];
  dataset_version: string;
  dataset_checksum: string;
  model_metadata: Record<string, unknown>;
  prompt_version: string;
  retrieval_configuration: Record<string, unknown>;
  environment_metadata: Record<string, unknown>;
  aggregate_metrics: Record<string, unknown> | null;
  failure: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export async function fetchEvaluationRuns(): Promise<EvaluationRun[]> {
  return apiRequest(
    "/api/v1/evaluation/runs",
    undefined,
    "Evaluation load failed",
  );
}
