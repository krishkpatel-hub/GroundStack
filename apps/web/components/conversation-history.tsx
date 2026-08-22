"use client";

import { Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { AppFrame } from "@/components/app-frame";
import {
  deleteConversation,
  fetchConversationMessages,
  fetchConversations,
  type Conversation,
  type ConversationMessage,
} from "@/lib/chat";

function groupLabel(value: string | null) {
  if (!value) return "No messages yet";
  const days = Math.floor((Date.now() - Date.parse(value)) / 86_400_000);
  if (days <= 1) return "Today and yesterday";
  if (days <= 7) return "Previous 7 days";
  if (days <= 30) return "Previous 30 days";
  return "Older";
}

export function ConversationHistory() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteArmed, setDeleteArmed] = useState<string | null>(null);

  useEffect(() => {
    void fetchConversations()
      .then((rows) => setItems(rows.filter((row) => !row.archived)))
      .catch((loadError) =>
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Conversation load failed",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selected) {
      return;
    }
    void fetchConversationMessages(selected)
      .then(setMessages)
      .catch(() => setMessages([]));
  }, [selected]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return [...items]
      .sort(
        (a, b) =>
          Date.parse(b.last_message_at ?? b.updated_at) -
          Date.parse(a.last_message_at ?? a.updated_at),
      )
      .filter((conversation) => {
        if (!term) return true;
        return (
          (conversation.title ?? "").toLowerCase().includes(term) ||
          messages.some((message) =>
            message.content.toLowerCase().includes(term),
          )
        );
      });
  }, [items, messages, query]);

  async function remove(id: string) {
    if (deleteArmed !== id) {
      setDeleteArmed(id);
      return;
    }
    await deleteConversation(id);
    setItems((current) => current.filter((item) => item.id !== id));
    setSelected(null);
    setDeleteArmed(null);
  }

  return (
    <AppFrame
      title="Conversation history"
      description="Search, inspect, and remove conversations owned by the current user."
    >
      <section className="two-column">
        <div>
          <label htmlFor="conversation-search" className="label">
            Search title or loaded message content
          </label>
          <div className="field-with-icon">
            <Search className="h-4 w-4" aria-hidden />
            <input
              id="conversation-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search conversations"
            />
          </div>
          {loading && (
            <p className="mt-4 text-sm text-[var(--graphite)]">
              Loading history.
            </p>
          )}
          {error && <div className="inline-alert mt-4">{error}</div>}
          {!loading && filtered.length === 0 && (
            <p className="mt-4 text-sm leading-6 text-[var(--graphite)]">
              No conversations match this view. Ask a question to create a
              conversation.
            </p>
          )}
          <div className="mt-4 space-y-5">
            {Array.from(
              new Set(filtered.map((item) => groupLabel(item.last_message_at))),
            ).map((group) => (
              <section key={group} aria-labelledby={`${group}-heading`}>
                <h2 id={`${group}-heading`} className="text-sm font-semibold">
                  {group}
                </h2>
                <div className="mt-2 space-y-1">
                  {filtered
                    .filter(
                      (item) => groupLabel(item.last_message_at) === group,
                    )
                    .map((conversation) => (
                      <button
                        key={conversation.id}
                        className={`conversation-button ${
                          selected === conversation.id
                            ? "conversation-active"
                            : ""
                        }`}
                        type="button"
                        onClick={() => setSelected(conversation.id)}
                      >
                        <span className="truncate">
                          {conversation.title || "Untitled conversation"}
                        </span>
                      </button>
                    ))}
                </div>
              </section>
            ))}
          </div>
        </div>
        <section
          aria-labelledby="history-detail-heading"
          className="section-band"
        >
          <h2 id="history-detail-heading" className="section-title">
            Selected conversation
          </h2>
          {!selected && (
            <p className="mt-3 text-sm leading-6 text-[var(--graphite)]">
              Choose a conversation to inspect messages and citations.
            </p>
          )}
          {selected && (
            <>
              <button
                className="button mt-4"
                type="button"
                onClick={() => void remove(selected)}
              >
                <Trash2 className="h-4 w-4" aria-hidden />
                {deleteArmed === selected
                  ? "Confirm delete selected conversation"
                  : "Delete selected conversation"}
              </button>
              {deleteArmed === selected && (
                <p className="mt-2 text-xs leading-5 text-[var(--danger)]">
                  This removes the conversation from your history and cannot be
                  undone here.
                </p>
              )}
              <div className="mt-4 space-y-4">
                {messages.map((message) => (
                  <article key={message.id} className="evidence-row">
                    <h3 className="text-sm font-semibold">{message.role}</h3>
                    <p className="mt-1 whitespace-pre-wrap text-sm leading-6">
                      {message.content}
                    </p>
                    {message.grounding_status && (
                      <span className="status-label mt-2">
                        {message.grounding_status}
                      </span>
                    )}
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
      </section>
    </AppFrame>
  );
}
