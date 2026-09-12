import { apiRequest } from "@/lib/api";

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
  return apiRequest(
    "/api/v1/training/candidates",
    undefined,
    "Training candidates failed",
  );
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
  return apiRequest(
    `/api/v1/training/candidates/${candidateId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Training update failed",
  );
}
