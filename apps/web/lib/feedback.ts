import { apiRequest } from "@/lib/api";

export const feedbackCategories = [
  "incorrect_answer",
  "incomplete_answer",
  "irrelevant_sources",
  "missing_citation",
  "incorrect_citation",
  "unsupported_claim",
  "unsafe_response",
  "too_verbose",
  "too_vague",
  "slow_response",
  "other",
] as const;

export type FeedbackCategory = (typeof feedbackCategories)[number];
export type FeedbackRating = "positive" | "negative";

export type FeedbackPayload = {
  rating: FeedbackRating;
  categories: FeedbackCategory[];
  comment?: string | null;
  suggested_correction?: string | null;
  citations_incorrect: boolean;
  reported_citation_ids: string[];
  client_request_id: string;
};

export type FeedbackResponse = FeedbackPayload & {
  id: string;
  message_id: string;
  conversation_id: string;
  created_at: string;
  updated_at: string;
};

export async function saveFeedback(
  messageId: string,
  payload: FeedbackPayload,
): Promise<FeedbackResponse> {
  return apiRequest(
    `/api/v1/messages/${messageId}/feedback`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Feedback save failed",
  );
}
