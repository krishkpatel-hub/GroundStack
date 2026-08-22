const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
  const response = await fetch(`${API_BASE_URL}/api/v1/evaluation/runs`, {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(`Evaluation load failed with ${response.status}`);
  return response.json() as Promise<EvaluationRun[]>;
}
