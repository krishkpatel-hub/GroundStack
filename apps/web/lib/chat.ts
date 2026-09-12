import {
  API_BASE_URL,
  apiErrorMessage,
  apiRequest,
  friendlyApiError,
} from "@/lib/api";
import { type Citation, type RetrievalFilters } from "@/lib/retrieval";

export type Conversation = {
  id: string;
  title: string | null;
  archived: boolean;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
};

export type ConversationMessage = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  status: string;
  content: string;
  grounding_status: string | null;
  retrieval_run_id: string | null;
  generation_run_id: string | null;
  provider: string | null;
  model: string | null;
  prompt_version: string | null;
  token_usage: Record<string, unknown> | null;
  failure: Record<string, unknown> | null;
  citations: string[];
  created_at: string;
  completed_at: string | null;
};

export type ChatStreamEvent = {
  event: string;
  data: {
    request_id?: string;
    sequence?: number;
    conversation_id?: string;
    user_message_id?: string;
    message_id?: string;
    retrieval_run_id?: string | null;
    citations?: Citation[];
    token?: string;
    answer?: string;
    grounding_status?: string;
    provider?: string;
    model?: string;
    usage?: Record<string, unknown>;
    category?: string;
    message?: string;
  };
};

export async function fetchConversations(
  options: { limit?: number; offset?: number; signal?: AbortSignal } = {},
): Promise<Conversation[]> {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 50),
    offset: String(options.offset ?? 0),
  });
  return apiRequest(
    `/api/v1/conversations?${params}`,
    {
      signal: options.signal,
    },
    "Conversation load failed",
  );
}

export async function createConversation(
  title?: string,
): Promise<Conversation> {
  return apiRequest(
    "/api/v1/conversations",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    },
    "Conversation create failed",
  );
}

export async function updateConversation(
  conversationId: string,
  payload: { title?: string; archived?: boolean },
): Promise<Conversation> {
  return apiRequest(
    `/api/v1/conversations/${conversationId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Conversation update failed",
  );
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  await apiRequest(
    `/api/v1/conversations/${conversationId}`,
    {
      method: "DELETE",
    },
    "Conversation delete failed",
  );
}

export async function fetchConversationMessages(
  conversationId: string,
  signal?: AbortSignal,
): Promise<ConversationMessage[]> {
  return apiRequest(
    `/api/v1/conversations/${conversationId}/messages`,
    { signal },
    "Message load failed",
  );
}

export async function* streamChat(
  payload: {
    conversation_id?: string | null;
    question: string;
    client_request_id?: string;
    filters: RetrievalFilters;
  },
  signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal,
    });
  } catch (error) {
    throw friendlyApiError(error, "Chat stream failed.");
  }

  if (!response.ok || !response.body) {
    throw new Error(
      await apiErrorMessage(
        response,
        `Chat stream failed with ${response.status}`,
      ),
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        const parsed = parseSseFrame(frame);
        if (parsed) yield parsed;
      }

      if (done) break;
    }

    const parsed = parseSseFrame(buffer);
    if (parsed) yield parsed;
  } finally {
    reader.releaseLock();
  }
}

function parseSseFrame(frame: string): ChatStreamEvent | null {
  const lines = frame.split("\n");
  let event = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
  }

  if (dataLines.length === 0) return null;
  return {
    event,
    data: JSON.parse(dataLines.join("\n")) as ChatStreamEvent["data"],
  };
}
