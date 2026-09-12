import { describe, expect, it, vi } from "vitest";

import {
  documentStatusLabel,
  fetchDocuments,
  fetchIngestionJob,
  MAX_UPLOAD_SIZE_BYTES,
  submitKnowledgeUrl,
  validateKnowledgeFile,
} from "@/lib/knowledge";
import { searchRetrieval } from "@/lib/retrieval";

describe("knowledge API utilities", () => {
  it("fetches paginated documents", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ total: 0, limit: 10, offset: 0, items: [] }),
    }) as unknown as typeof fetch;

    const page = await fetchDocuments(10, 0);

    expect(page.total).toBe(0);
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/documents?limit=10&offset=0",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("submits url ingestion as json", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: "job", status: "queued" }),
    }) as unknown as typeof fetch;

    await submitKnowledgeUrl("https://docs.example.com/a");

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/ingestions/url",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws on job fetch failure", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ error: { message: "Ingestion job not found." } }),
    }) as unknown as typeof fetch;
    await expect(fetchIngestionJob("missing")).rejects.toThrow(
      "Ingestion job not found.",
    );
  });

  it("validates obvious unsupported uploads before network submission", () => {
    const unsupported = new File(["hello"], "notes.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const markdown = new File(["# Setup"], "setup.md", {
      type: "text/markdown",
    });
    const oversized = new File(["x"], "large.md");
    Object.defineProperty(oversized, "size", {
      value: MAX_UPLOAD_SIZE_BYTES + 1,
    });

    expect(validateKnowledgeFile(unsupported)).toContain(
      "not a supported document type",
    );
    expect(validateKnowledgeFile(oversized)).toContain("10 MB upload limit");
    expect(validateKnowledgeFile(markdown)).toBeNull();
  });

  it("maps internal document source status to user-facing labels", () => {
    expect(documentStatusLabel("active")).toBe("Ready");
    expect(documentStatusLabel("queued")).toBe("Processing");
    expect(documentStatusLabel("failed")).toBe("Failed");
  });

  it("submits retrieval search with filters", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        retrieval_run_id: "run",
        normalized_query: "database",
        result_count: 0,
        evidence_found: false,
        reranking_applied: false,
        degraded_mode: null,
        applied_filters: {
          source_types: ["file"],
          source_ids: [],
          document_ids: [],
        },
        citations: [],
        timings_ms: { total: 1 },
        debug: null,
      }),
    }) as unknown as typeof fetch;

    await searchRetrieval({
      query: "database",
      top_k: 8,
      filters: { source_types: ["file"], source_ids: [], document_ids: [] },
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/retrieval/search",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
