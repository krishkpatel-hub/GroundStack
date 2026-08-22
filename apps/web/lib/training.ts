const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type TrainingCandidate = {
  id: string;
  message_id: string;
  feedback_id: string | null;
  status: string;
  proposed_question: string;
  evidence_snapshot: Array<Record<string, unknown>>;
  proposed_answer: string;
  citation_references: string[];
  redaction_status: string;
  provenance_status: string;
  reviewer_notes: string | null;
  reviewer_identifier: string | null;
  dataset_export_status: string;
  created_at: string;
  reviewed_at: string | null;
};

export async function fetchTrainingCandidates(): Promise<TrainingCandidate[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/training/candidates`, {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(`Training candidates failed with ${response.status}`);
  return response.json() as Promise<TrainingCandidate[]>;
}

export async function updateTrainingCandidate(
  candidateId: string,
  payload: Partial<
    Pick<
      TrainingCandidate,
      | "status"
      | "proposed_question"
      | "proposed_answer"
      | "redaction_status"
      | "provenance_status"
      | "reviewer_notes"
      | "reviewer_identifier"
    >
  >,
): Promise<TrainingCandidate> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/training/candidates/${candidateId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    },
  );
  if (!response.ok)
    throw new Error(`Training update failed with ${response.status}`);
  return response.json() as Promise<TrainingCandidate>;
}
