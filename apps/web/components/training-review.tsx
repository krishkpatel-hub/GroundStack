"use client";

import { Check, Edit3, RefreshCw, X } from "lucide-react";
import { useEffect, useState } from "react";

import { AppFrame } from "@/components/app-frame";
import {
  fetchTrainingCandidates,
  updateTrainingCandidate,
  type TrainingCandidate,
} from "@/lib/training";

export function TrainingReview() {
  const [items, setItems] = useState<TrainingCandidate[]>([]);
  const [selected, setSelected] = useState<TrainingCandidate | null>(null);
  const [draft, setDraft] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const rows = await fetchTrainingCandidates();
      setItems(rows);
      setSelected(rows[0] ?? null);
      setDraft(rows[0]?.proposed_answer ?? "");
      setNotes(rows[0]?.reviewer_notes ?? "");
      setError(null);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Training review failed",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, []);

  async function review(status: "approved" | "rejected") {
    if (!selected) return;
    const updated = await updateTrainingCandidate(selected.id, {
      status,
      proposed_answer: draft,
      redaction_status:
        status === "approved" ? "approved" : selected.redaction_status,
      provenance_status:
        status === "approved" ? "approved" : selected.provenance_status,
      reviewer_notes: notes,
      reviewer_identifier: "groundstack-admin",
    });
    setItems((current) =>
      current.map((item) => (item.id === updated.id ? updated : item)),
    );
    setSelected(updated);
  }

  return (
    <AppFrame
      title="Training dataset review"
      description="Review feedback-derived candidates before any example can enter a training dataset."
      actions={
        <button className="button" type="button" onClick={() => void load()}>
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh
        </button>
      }
    >
      {loading && (
        <p className="text-sm text-[var(--graphite)]">Loading candidates.</p>
      )}
      {error && <div className="inline-alert">{error}</div>}
      {!loading && items.length === 0 && (
        <section className="empty-chat">
          <h2 className="section-title">No training candidates</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--graphite)]">
            Negative feedback with suggested corrections can create candidates,
            but nothing enters training data until a human approves redaction
            and provenance.
          </p>
        </section>
      )}
      {items.length > 0 && (
        <section className="two-column">
          <div className="table-wrap">
            <table className="data-table">
              <caption>Training candidates requiring human review</caption>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Question</th>
                  <th>Provenance</th>
                  <th>Redaction</th>
                </tr>
              </thead>
              <tbody>
                {items.map((candidate) => (
                  <tr
                    key={candidate.id}
                    className={
                      selected?.id === candidate.id ? "selected-row" : ""
                    }
                  >
                    <td>
                      <button
                        className="button min-h-9"
                        type="button"
                        onClick={() => {
                          setSelected(candidate);
                          setDraft(candidate.proposed_answer);
                          setNotes(candidate.reviewer_notes ?? "");
                        }}
                      >
                        {candidate.status}
                      </button>
                    </td>
                    <td>
                      {candidate.proposed_question ||
                        "Question snapshot not recorded"}
                    </td>
                    <td>{candidate.provenance_status}</td>
                    <td>{candidate.redaction_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {selected && (
            <section
              className="section-band"
              aria-labelledby="candidate-heading"
            >
              <h2 id="candidate-heading" className="section-title">
                Candidate detail
              </h2>
              <dl className="document-facts mt-4">
                <div>
                  <dt>Message</dt>
                  <dd>{selected.message_id}</dd>
                </div>
                <div>
                  <dt>Citations</dt>
                  <dd>
                    {selected.citation_references.join(", ") || "None recorded"}
                  </dd>
                </div>
                <div>
                  <dt>Duplicate check</dt>
                  <dd>Enforced by message and feedback uniqueness.</dd>
                </div>
              </dl>
              <label htmlFor="candidate-answer" className="label mt-4">
                Proposed corrected answer
              </label>
              <textarea
                id="candidate-answer"
                className="field min-h-40"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
              />
              <label htmlFor="review-notes" className="label mt-4">
                Review notes
              </label>
              <textarea
                id="review-notes"
                className="field"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  className="button button-primary"
                  type="button"
                  onClick={() => void review("approved")}
                >
                  <Check className="h-4 w-4" aria-hidden />
                  Approve reviewed candidate
                </button>
                <button
                  className="button"
                  type="button"
                  onClick={() => void review("rejected")}
                >
                  <X className="h-4 w-4" aria-hidden />
                  Reject
                </button>
                <span className="status-label">
                  <Edit3 className="h-4 w-4" aria-hidden />
                  Editable before approval
                </span>
              </div>
            </section>
          )}
        </section>
      )}
    </AppFrame>
  );
}
