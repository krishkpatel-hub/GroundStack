"use client";

import {
  AlertTriangle,
  BookOpen,
  Copy,
  Pencil,
  ThumbsDown,
  ThumbsUp,
  LoaderCircle,
  MessageSquarePlus,
  Trash2,
  RotateCcw,
  Send,
  Square,
  X,
} from "lucide-react";
import Link from "next/link";
import { FormEvent, memo, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AppFrame } from "@/components/app-frame";
import {
  fetchConversationMessages,
  fetchConversations,
  deleteConversation,
  streamChat,
  updateConversation,
  type Conversation,
} from "@/lib/chat";
import { fetchDocuments, type DocumentItem } from "@/lib/knowledge";
import {
  feedbackCategories,
  saveFeedback,
  type FeedbackCategory,
  type FeedbackRating,
} from "@/lib/feedback";
import { type Citation } from "@/lib/retrieval";

type ChatRole = "user" | "assistant";

type LocalMessage = {
  localId: string;
  id?: string;
  role: ChatRole;
  content: string;
  status: "streaming" | "completed" | "failed";
  groundingStatus?: string | null;
  citations: Citation[];
  citationIds: string[];
};

type StreamStage =
  | "Idle"
  | "Retrieving evidence"
  | "Generating answer"
  | "Repairing citations"
  | "Completed"
  | "Stopped"
  | "Failed";

function newLocalId(prefix: string) {
  return `${prefix}-${globalThis.crypto?.randomUUID?.() ?? Date.now()}`;
}

export function AppShell({
  initialQuestion = "",
}: {
  initialQuestion?: string;
}) {
  const [question, setQuestion] = useState(() => initialQuestion);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [historySearch, setHistorySearch] = useState("");
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const [deleteArmed, setDeleteArmed] = useState(false);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [sourceType, setSourceType] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [stage, setStage] = useState<StreamStage>("Idle");
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [lastQuestion, setLastQuestion] = useState("");
  const [announce, setAnnounce] = useState("Ready");
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const citationButtonRef = useRef<HTMLButtonElement | null>(null);

  const loading =
    stage === "Retrieving evidence" || stage === "Generating answer";

  async function loadConversations() {
    const items = await fetchConversations().catch(() => []);
    setConversations(items.filter((item) => !item.archived));
  }

  useEffect(() => {
    let active = true;
    fetchConversations()
      .then((items) => {
        if (active) setConversations(items.filter((item) => !item.archived));
      })
      .catch(() => {
        if (active) setConversations([]);
      });
    fetchDocuments(100, 0)
      .then((page) => {
        if (active) setDocuments(page.items);
      })
      .catch(() => {
        if (active) setDocuments([]);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (stage === "Completed" || stage === "Failed") {
      bottomRef.current?.scrollIntoView({ block: "nearest" });
    }
  }, [stage]);

  useEffect(() => {
    if (!initialQuestion) return;
    const timeout = window.setTimeout(() => setQuestion(initialQuestion), 0);
    return () => window.clearTimeout(timeout);
  }, [initialQuestion]);

  const sourceTypes = useMemo(
    () =>
      Array.from(
        new Set(documents.map((document) => document.source_type)),
      ).sort(),
    [documents],
  );
  const sourceOptions = useMemo(
    () =>
      Array.from(
        new Map(
          documents
            .filter(
              (document) => !sourceType || document.source_type === sourceType,
            )
            .map((document) => [document.source_id, document]),
        ).values(),
      ),
    [documents, sourceType],
  );

  const filters = useMemo(
    () => ({
      source_types: sourceType ? [sourceType] : [],
      source_ids: sourceId ? [sourceId] : [],
      document_ids: [],
    }),
    [sourceId, sourceType],
  );

  const selectedConversation = conversations.find(
    (conversation) => conversation.id === conversationId,
  );

  const filteredConversations = useMemo(() => {
    const term = historySearch.trim().toLowerCase();
    const sorted = [...conversations].sort(
      (a, b) =>
        Date.parse(b.last_message_at ?? b.updated_at) -
        Date.parse(a.last_message_at ?? a.updated_at),
    );
    if (!term) return sorted;
    return sorted.filter((conversation) =>
      (conversation.title ?? "Untitled conversation")
        .toLowerCase()
        .includes(term),
    );
  }, [conversations, historySearch]);

  async function selectConversation(nextConversationId: string) {
    abortRef.current?.abort();
    setConversationId(nextConversationId);
    setError(null);
    setStage("Idle");
    setAnnounce("Conversation loaded");
    setDeleteArmed(false);
    setEditingTitle(false);
    const rows = await fetchConversationMessages(nextConversationId);
    setMessages(
      rows
        .filter((row) => row.role === "user" || row.role === "assistant")
        .map((row) => ({
          localId: row.id,
          id: row.id,
          role: row.role as ChatRole,
          content: row.content,
          status: row.status === "completed" ? "completed" : "failed",
          groundingStatus: row.grounding_status,
          citations: [],
          citationIds: row.citations,
        })),
    );
  }

  function startNewConversation() {
    abortRef.current?.abort();
    abortRef.current = null;
    setConversationId(null);
    setMessages([]);
    setQuestion("");
    setError(null);
    setStage("Idle");
    setAnnounce("New conversation ready");
    setDeleteArmed(false);
    setEditingTitle(false);
  }

  async function renameSelectedConversation() {
    if (!conversationId || !titleDraft.trim()) return;
    const updated = await updateConversation(conversationId, {
      title: titleDraft.trim(),
    });
    setConversations((current) =>
      current.map((item) => (item.id === updated.id ? updated : item)),
    );
    setEditingTitle(false);
    setAnnounce("Conversation renamed");
  }

  async function deleteSelectedConversation() {
    if (!conversationId || !deleteArmed) return;
    await deleteConversation(conversationId);
    setConversations((current) =>
      current.filter((item) => item.id !== conversationId),
    );
    startNewConversation();
    setAnnounce(
      "Conversation deleted. Messages were archived for this workspace.",
    );
  }

  async function submitChat(
    event?: FormEvent<HTMLFormElement>,
    retry?: string,
  ) {
    event?.preventDefault();
    const trimmed = (retry ?? question).trim();
    if (!trimmed || loading) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const userLocalId = newLocalId("user");
    const assistantLocalId = newLocalId("assistant");

    setLastQuestion(trimmed);
    setQuestion("");
    setError(null);
    setStage("Retrieving evidence");
    setAnnounce("Retrieving supporting sources");
    setMessages((current) => [
      ...current,
      {
        localId: userLocalId,
        role: "user",
        content: trimmed,
        status: "completed",
        citations: [],
        citationIds: [],
      },
      {
        localId: assistantLocalId,
        role: "assistant",
        content: "",
        status: "streaming",
        groundingStatus: null,
        citations: [],
        citationIds: [],
      },
    ]);

    try {
      for await (const item of streamChat(
        {
          conversation_id: conversationId,
          question: trimmed,
          client_request_id: newLocalId("request"),
          filters,
        },
        controller.signal,
      )) {
        if (item.event === "conversation" && item.data.conversation_id) {
          setConversationId(item.data.conversation_id);
        }
        if (item.event === "retrieval_completed") {
          setStage("Generating answer");
          setAnnounce("Evidence retrieved. Generating answer.");
          const citations = item.data.citations ?? [];
          setMessages((current) =>
            updateAssistant(current, assistantLocalId, {
              citations,
              citationIds: citations.map((citation) => citation.citation_id),
            }),
          );
        }
        if (item.event === "generation_started") setStage("Generating answer");
        if (item.event === "repair_started") {
          setStage("Repairing citations");
          setAnnounce("Validating citations");
        }
        if (item.event === "token" && item.data.token) {
          setMessages((current) =>
            updateAssistant(current, assistantLocalId, (message) => ({
              content: message.content + item.data.token,
            })),
          );
        }
        if (item.event === "canonical_answer") {
          setStage("Completed");
          setAnnounce("Answer completed");
          setMessages((current) =>
            updateAssistant(current, assistantLocalId, {
              id: item.data.message_id,
              content: item.data.answer ?? "",
              status: "completed",
              groundingStatus: item.data.grounding_status,
            }),
          );
        }
        if (item.event === "completed") {
          setStage("Completed");
          void loadConversations();
        }
        if (item.event === "error") {
          throw new Error(item.data.message ?? "Answer generation failed");
        }
      }
    } catch (chatError) {
      if (
        chatError instanceof DOMException &&
        chatError.name === "AbortError"
      ) {
        setStage("Stopped");
        setAnnounce("Generation stopped. Partial answer was preserved.");
        setMessages((current) =>
          updateAssistant(current, assistantLocalId, { status: "failed" }),
        );
        return;
      }
      const message =
        chatError instanceof Error
          ? chatError.message
          : "Answer generation failed";
      setError(message);
      setStage("Failed");
      setAnnounce(
        "Generation failed. Your question and partial output were preserved.",
      );
      setMessages((current) =>
        updateAssistant(current, assistantLocalId, {
          content: message,
          status: "failed",
          groundingStatus: "generation_failed",
        }),
      );
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
    }
  }

  function stopGeneration() {
    abortRef.current?.abort();
    abortRef.current = null;
  }

  return (
    <AppFrame
      title="Ask GroundStack"
      description="Ask grounded questions, inspect cited source passages, and keep conversation history under your own account."
      actions={
        <button className="button" type="button" onClick={startNewConversation}>
          <MessageSquarePlus className="h-4 w-4" aria-hidden />
          New chat
        </button>
      }
    >
      <div className="chat-grid">
        <aside className="conversation-panel" aria-label="Conversation history">
          <div className="flex items-center justify-between gap-2">
            <h2 className="section-title">Conversations</h2>
            <button
              className="button h-9 min-h-9 w-9 p-0"
              type="button"
              aria-label="Refresh conversations"
              onClick={() => void loadConversations()}
            >
              <RotateCcw className="h-4 w-4" aria-hidden />
            </button>
          </div>
          <label htmlFor="history-search" className="label mt-4">
            Search history
          </label>
          <input
            id="history-search"
            className="field h-10 min-h-10"
            value={historySearch}
            onChange={(event) => setHistorySearch(event.target.value)}
            placeholder="Title or first question"
          />
          {selectedConversation && (
            <div className="mt-4 border-t border-[var(--border)] pt-4">
              {editingTitle ? (
                <div className="space-y-2">
                  <label htmlFor="conversation-title" className="label">
                    Conversation title
                  </label>
                  <input
                    id="conversation-title"
                    className="field"
                    value={titleDraft}
                    onChange={(event) => setTitleDraft(event.target.value)}
                  />
                  <div className="flex gap-2">
                    <button
                      className="button button-primary min-h-9"
                      type="button"
                      onClick={() => void renameSelectedConversation()}
                    >
                      Save
                    </button>
                    <button
                      className="button min-h-9"
                      type="button"
                      onClick={() => setEditingTitle(false)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  className="button min-h-9 w-full"
                  type="button"
                  onClick={() => {
                    setTitleDraft(selectedConversation.title ?? "");
                    setEditingTitle(true);
                  }}
                >
                  <Pencil className="h-4 w-4" aria-hidden />
                  Rename selected
                </button>
              )}
              <div className="mt-2">
                <button
                  className="button min-h-9 w-full"
                  type="button"
                  onClick={() =>
                    deleteArmed
                      ? void deleteSelectedConversation()
                      : setDeleteArmed(true)
                  }
                >
                  <Trash2 className="h-4 w-4" aria-hidden />
                  {deleteArmed
                    ? "Confirm delete selected conversation"
                    : "Delete selected conversation"}
                </button>
                {deleteArmed && (
                  <p className="mt-2 text-xs leading-5 text-[var(--danger)]">
                    This removes the conversation from your history. It is not
                    reversible from this interface.
                  </p>
                )}
              </div>
            </div>
          )}
          <div className="mt-3 space-y-1">
            {filteredConversations.length === 0 && (
              <p className="text-sm leading-6 text-[var(--graphite)]">
                No matching conversations. Start a new question to create one.
              </p>
            )}
            {filteredConversations.map((conversation) => (
              <button
                key={conversation.id}
                className={`conversation-button ${
                  conversation.id === conversationId
                    ? "conversation-active"
                    : ""
                }`}
                type="button"
                onClick={() => void selectConversation(conversation.id)}
              >
                <span className="truncate">
                  {conversation.title ?? "Untitled conversation"}
                </span>
              </button>
            ))}
          </div>
        </aside>

        <section className="chat-surface" aria-label="Grounded conversation">
          <div className="sr-only" aria-live="polite">
            {announce}
          </div>
          <div className="message-list">
            {messages.length === 0 && (
              <div className="empty-chat">
                <h2 className="text-xl font-semibold">Ask from your sources</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--graphite)]">
                  GroundStack will retrieve evidence, stream a LLaMA-backed
                  answer, and reject unsupported or fabricated citations.
                </p>
              </div>
            )}
            {messages.map((message) => (
              <MessageBubble
                key={message.localId}
                message={message}
                onOpenCitation={(citation, button) => {
                  citationButtonRef.current = button;
                  setActiveCitation(citation);
                }}
              />
            ))}
            <div ref={bottomRef} />
          </div>

          {error && (
            <div className="inline-alert mx-4 mb-3" role="alert">
              <AlertTriangle className="inline h-4 w-4" aria-hidden /> {error}
            </div>
          )}

          <form
            className="composer"
            onSubmit={(event) => void submitChat(event)}
          >
            <div className="flex items-center justify-between gap-3 pb-2">
              <span className="status-label" aria-live="polite">
                {loading && (
                  <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
                )}
                {stage}
              </span>
              {lastQuestion && !loading && (
                <button
                  className="button h-9 min-h-9"
                  type="button"
                  onClick={() => void submitChat(undefined, lastQuestion)}
                >
                  <RotateCcw className="h-4 w-4" aria-hidden />
                  Retry
                </button>
              )}
            </div>
            <textarea
              aria-label="Question"
              aria-describedby="composer-help"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submitChat();
                }
              }}
              placeholder="Ask a grounded question..."
              className="field composer-field"
              disabled={loading}
              maxLength={1200}
            />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <p
                id="composer-help"
                className="text-xs leading-5 text-[var(--graphite)]"
              >
                Enter sends. Shift+Enter adds a line. {1200 - question.length}{" "}
                characters remaining. Duplicate submissions are blocked while
                generation is active.
              </p>
              <div className="grid min-w-[220px] flex-1 gap-2 md:grid-cols-2">
                <select
                  className="field h-10 min-h-10"
                  value={sourceType}
                  onChange={(event) => {
                    setSourceType(event.target.value);
                    setSourceId("");
                  }}
                  aria-label="Source type filter"
                >
                  <option value="">All source types</option>
                  {sourceTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <select
                  className="field h-10 min-h-10"
                  value={sourceId}
                  onChange={(event) => setSourceId(event.target.value)}
                  aria-label="Source filter"
                >
                  <option value="">All sources</option>
                  {sourceOptions.map((document) => (
                    <option key={document.source_id} value={document.source_id}>
                      {document.display_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                {loading && (
                  <button
                    className="button"
                    type="button"
                    onClick={stopGeneration}
                  >
                    <Square className="h-4 w-4" aria-hidden />
                    Stop
                  </button>
                )}
                <button
                  className="button button-primary"
                  type="submit"
                  disabled={loading || !question.trim()}
                >
                  <Send className="h-4 w-4" aria-hidden />
                  Send
                </button>
              </div>
            </div>
          </form>
        </section>
      </div>
      {activeCitation && (
        <SourcePanel
          citation={activeCitation}
          onClose={() => {
            setActiveCitation(null);
            citationButtonRef.current?.focus();
          }}
        />
      )}
    </AppFrame>
  );
}

function updateAssistant(
  messages: LocalMessage[],
  localId: string,
  patch:
    Partial<LocalMessage> | ((message: LocalMessage) => Partial<LocalMessage>),
) {
  return messages.map((message) => {
    if (message.localId !== localId) return message;
    const nextPatch = typeof patch === "function" ? patch(message) : patch;
    return { ...message, ...nextPatch };
  });
}

const MessageBubble = memo(function MessageBubble({
  message,
  onOpenCitation,
}: {
  message: LocalMessage;
  onOpenCitation: (citation: Citation, button: HTMLButtonElement) => void;
}) {
  const citationMap = new Map(
    message.citations.map((citation) => [citation.citation_id, citation]),
  );

  return (
    <article className={`message message-${message.role}`}>
      <div className="message-label">
        {message.role === "user" ? "You" : "GroundStack"}
        {message.status === "streaming" && (
          <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
        )}
      </div>
      <div className="message-body">
        {message.role === "assistant" ? (
          <Markdown
            content={message.content || "Preparing grounded answer..."}
          />
        ) : (
          <p>{message.content}</p>
        )}
      </div>
      {message.role === "assistant" &&
        (message.citations.length > 0 || message.citationIds.length > 0) && (
          <div className="citation-strip">
            {(message.citations.length
              ? message.citations.map((citation) => citation.citation_id)
              : message.citationIds
            ).map((citationId) => {
              const citation = citationMap.get(citationId);
              return (
                <div key={citationId} className="citation-item">
                  <button
                    className="button min-h-8"
                    type="button"
                    onClick={(event) =>
                      citation && onOpenCitation(citation, event.currentTarget)
                    }
                  >
                    <BookOpen className="h-4 w-4" aria-hidden />[{citationId}]
                  </button>
                </div>
              );
            })}
          </div>
        )}
      {message.groundingStatus && (
        <span className="status-label mt-3">{message.groundingStatus}</span>
      )}
      {message.role === "assistant" &&
        message.status === "completed" &&
        message.id && <FeedbackControls message={message} />}
    </article>
  );
});

function SourcePanel({
  citation,
  onClose,
}: {
  citation: Citation;
  onClose: () => void;
}) {
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    panelRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="dialog-layer" role="presentation">
      <button
        className="dialog-backdrop"
        aria-label="Close source viewer"
        onClick={onClose}
      />
      <section
        ref={panelRef}
        className="source-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="source-panel-title"
        tabIndex={-1}
      >
        <div className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-3">
          <div>
            <h2 id="source-panel-title" className="section-title">
              {citation.title || "Source passage"}
            </h2>
            <p className="mt-1 text-sm leading-6 text-[var(--graphite)]">
              {citation.source_display_name}
              {citation.section_path ? `, ${citation.section_path}` : ""}
              {citation.page_number ? `, page ${citation.page_number}` : ""}
            </p>
          </div>
          <button
            className="button h-9 min-h-9 w-9 p-0"
            type="button"
            onClick={onClose}
          >
            <X className="h-4 w-4" aria-hidden />
            <span className="sr-only">Close source viewer</span>
          </button>
        </div>
        <dl className="document-facts mt-4">
          <div>
            <dt>Citation</dt>
            <dd>{citation.citation_id}</dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>
              {citation.document_version
                ? `v${citation.document_version}`
                : "Not recorded"}
            </dd>
          </div>
        </dl>
        <p className="mt-4 whitespace-pre-wrap rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--canvas)] p-3 text-sm leading-6">
          {citation.excerpt || "No excerpt was returned for this citation."}
        </p>
        <Link
          className="button mt-4 no-underline"
          href={`/sources?document=${citation.document_id}`}
        >
          Open source inventory
        </Link>
      </section>
    </div>
  );
}

function FeedbackControls({ message }: { message: LocalMessage }) {
  const [rating, setRating] = useState<FeedbackRating | null>(null);
  const [categories, setCategories] = useState<FeedbackCategory[]>([]);
  const [comment, setComment] = useState("");
  const [correction, setCorrection] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const clientRequestId = useMemo(
    () =>
      `feedback-${message.id}-${globalThis.crypto?.randomUUID?.() ?? "local"}`,
    [message.id],
  );

  function toggleCategory(category: FeedbackCategory) {
    setCategories((current) =>
      current.includes(category)
        ? current.filter((item) => item !== category)
        : [...current, category],
    );
  }

  async function submit(nextRating = rating) {
    if (!message.id || !nextRating) return;
    setSaving(true);
    setError(null);
    try {
      await saveFeedback(message.id, {
        rating: nextRating,
        categories: nextRating === "negative" ? categories : [],
        comment: comment.trim() || null,
        suggested_correction: correction.trim() || null,
        citations_incorrect:
          nextRating === "negative" &&
          categories.includes("incorrect_citation"),
        reported_citation_ids:
          nextRating === "negative" && categories.includes("incorrect_citation")
            ? message.citationIds
            : [],
        client_request_id: clientRequestId,
      });
      setSaved(true);
    } catch (feedbackError) {
      setError(
        feedbackError instanceof Error
          ? feedbackError.message
          : "Feedback save failed",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="feedback-panel" aria-label="Answer feedback">
      <div className="feedback-actions">
        <button
          className={`button min-h-9 ${rating === "positive" ? "button-selected" : ""}`}
          type="button"
          aria-pressed={rating === "positive"}
          onClick={() => {
            setRating("positive");
            void submit("positive");
          }}
        >
          <ThumbsUp className="h-4 w-4" aria-hidden />
          Helpful
        </button>
        <button
          className={`button min-h-9 ${rating === "negative" ? "button-selected" : ""}`}
          type="button"
          aria-pressed={rating === "negative"}
          onClick={() => {
            setRating("negative");
            setSaved(false);
          }}
        >
          <ThumbsDown className="h-4 w-4" aria-hidden />
          Needs work
        </button>
        <span className="status-label" aria-live="polite">
          {saving ? "Saving" : saved ? "Saved" : ""}
        </span>
      </div>
      {rating === "negative" && (
        <div className="feedback-detail">
          <div className="feedback-category-grid">
            {feedbackCategories.map((category) => (
              <label key={category} className="check-row">
                <input
                  type="checkbox"
                  checked={categories.includes(category)}
                  onChange={() => toggleCategory(category)}
                />
                <span>{category.replaceAll("_", " ")}</span>
              </label>
            ))}
          </div>
          <textarea
            className="field"
            value={comment}
            maxLength={1000}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Optional comment"
          />
          <textarea
            className="field"
            value={correction}
            maxLength={3000}
            onChange={(event) => setCorrection(event.target.value)}
            placeholder="Optional suggested correction"
          />
          <button
            className="button button-primary min-h-9"
            type="button"
            disabled={saving}
            onClick={() => void submit()}
          >
            Save feedback
          </button>
        </div>
      )}
      {error && <div className="inline-alert mt-2">{error}</div>}
    </div>
  );
}

function Markdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children }) => (
          <a href={safeHref(href)} rel="noreferrer" target="_blank">
            {children}
          </a>
        ),
        code: CodeRenderer,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function CodeRenderer({
  children,
  className,
}: {
  children?: React.ReactNode;
  className?: string;
}) {
  const code = String(children ?? "").replace(/\n$/, "");
  const inline = !className;
  if (inline) return <code>{children}</code>;
  return <CodeBlock code={code} />;
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="code-block">
      <button
        className="button code-copy"
        type="button"
        onClick={() => {
          void navigator.clipboard.writeText(code).then(() => {
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1200);
          });
        }}
      >
        <Copy className="h-4 w-4" aria-hidden />
        {copied ? "Copied" : "Copy"}
      </button>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

function safeHref(href?: string) {
  if (!href) return "#";
  try {
    const url = new URL(href, window.location.href);
    if (url.protocol === "http:" || url.protocol === "https:") return href;
  } catch {
    return "#";
  }
  return "#";
}
