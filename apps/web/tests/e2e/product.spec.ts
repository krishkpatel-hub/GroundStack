import { AxeBuilder } from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const conversationId = "11111111-1111-1111-1111-111111111111";
const messageId = "22222222-2222-2222-2222-222222222222";
const documentId = "33333333-3333-3333-3333-333333333333";

async function mockApi(page: Page, role: "anonymous" | "admin" = "admin") {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      json:
        role === "admin"
          ? {
              authenticated: true,
              anonymous: false,
              subject: "admin",
              roles: ["admin"],
              admin: true,
            }
          : {
              authenticated: false,
              anonymous: true,
              roles: ["demo_anonymous"],
              admin: false,
            },
    }),
  );
  await page.route("**/api/v1/system/status", (route) =>
    route.fulfill({
      json: {
        status: "ok",
        database: { reachable: true },
        model: { reachable: true },
      },
    }),
  );
  await page.route("**/api/v1/conversations?**", (route) =>
    route.fulfill({
      json: [
        {
          id: conversationId,
          title: "Demo: pgvector setup",
          archived: false,
          created_at: "2026-08-19T12:00:00Z",
          updated_at: "2026-08-19T12:10:00Z",
          last_message_at: "2026-08-19T12:10:00Z",
        },
      ],
    }),
  );
  await page.route(
    `**/api/v1/conversations/${conversationId}/messages`,
    (route) =>
      route.fulfill({
        json: [
          {
            id: "u1",
            conversation_id: conversationId,
            role: "user",
            status: "completed",
            content: "How do I configure pgvector for GroundStack?",
            grounding_status: null,
            retrieval_run_id: null,
            generation_run_id: null,
            provider: null,
            model: null,
            prompt_version: null,
            token_usage: null,
            failure: null,
            citations: [],
            created_at: "2026-08-19T12:00:00Z",
            completed_at: "2026-08-19T12:00:00Z",
          },
        ],
      }),
  );
  await page.route("**/api/v1/conversations/*", (route) =>
    route.fulfill({
      status: route.request().method() === "DELETE" ? 204 : 200,
      json: {},
    }),
  );
  await page.route("**/api/v1/documents?**", (route) =>
    route.fulfill({
      json: {
        total: 1,
        limit: 20,
        offset: 0,
        items: [
          {
            id: documentId,
            source_id: "44444444-4444-4444-4444-444444444444",
            source_type: "file",
            display_name: "setup.md",
            source_status: "ready",
            version: 1,
            title: "GroundStack setup",
            mime_type: "text/markdown",
            content_checksum: "demo-checksum",
            chunk_count: 2,
            ingested_at: "2026-08-19T12:00:00Z",
          },
        ],
      },
    }),
  );
  await page.route(`**/api/v1/documents/${documentId}/chunks?**`, (route) =>
    route.fulfill({
      json: {
        total: 1,
        limit: 10,
        offset: 0,
        items: [
          {
            id: "55555555-5555-5555-5555-555555555555",
            document_id: documentId,
            position: 1,
            heading_path: ["Setup"],
            content: "Run migrations after starting PostgreSQL with pgvector.",
            token_count: 12,
            chunk_checksum: "chunk",
            embedding_model: "demo",
            created_at: "2026-08-19T12:00:00Z",
          },
        ],
      },
    }),
  );
  await page.route("**/api/v1/chat/stream", (route) =>
    route.fulfill({
      headers: { "content-type": "text/event-stream" },
      body: [
        `event: conversation\ndata: {"conversation_id":"${conversationId}"}\n\n`,
        `event: retrieval_completed\ndata: {"citations":[{"citation_id":"S1","source_id":"44444444-4444-4444-4444-444444444444","document_id":"${documentId}","document_version":1,"chunk_id":"55555555-5555-5555-5555-555555555555","title":"GroundStack setup","source_display_name":"setup.md","source_type":"file","source_uri":null,"section_path":"Setup","page_number":null,"excerpt":"Run migrations after starting PostgreSQL with pgvector.","final_rank":1}]}\n\n`,
        `event: generation_started\ndata: {}\n\n`,
        `event: token\ndata: {"token":"Run migrations after starting PostgreSQL with pgvector. [S1]"}\n\n`,
        `event: canonical_answer\ndata: {"message_id":"${messageId}","answer":"Run migrations after starting PostgreSQL with pgvector. [S1]","grounding_status":"grounded"}\n\n`,
        `event: completed\ndata: {}\n\n`,
      ].join(""),
    }),
  );
  await page.route(`**/api/v1/messages/${messageId}/feedback`, (route) =>
    route.fulfill({
      json: {
        id: "f1",
        message_id: messageId,
        conversation_id: conversationId,
      },
    }),
  );
  await page.route("**/api/v1/evaluation/runs", (route) =>
    route.fulfill({
      json: [
        {
          id: "66666666-6666-6666-6666-666666666666",
          name: "Demo evaluation",
          status: "completed",
          suite_names: ["generation"],
          dataset_version: "demo-v1",
          dataset_checksum: "demo",
          model_metadata: { provider: "demo" },
          prompt_version: "grounded_answer/v1",
          retrieval_configuration: { top_k: 8 },
          environment_metadata: { report_path: "evaluation/reports/demo.json" },
          aggregate_metrics: { pass_rate: 1, sample_count: 4 },
          failure: null,
          created_at: "2026-08-19T12:00:00Z",
          started_at: "2026-08-19T12:00:00Z",
          completed_at: "2026-08-19T12:00:01Z",
        },
      ],
    }),
  );
  await page.route("**/api/v1/training/candidates", (route) =>
    route.fulfill({
      json: [
        {
          id: "77777777-7777-7777-7777-777777777777",
          message_id: messageId,
          feedback_id: "88888888-8888-8888-8888-888888888888",
          status: "pending",
          proposed_question: "How do I configure pgvector?",
          evidence_snapshot: [{ citation_id: "S1" }],
          proposed_answer: "Run migrations after PostgreSQL starts.",
          citation_references: ["S1"],
          redaction_status: "pending",
          provenance_status: "pending",
          reviewer_notes: null,
          reviewer_identifier: null,
          dataset_export_status: "not_exported",
          created_at: "2026-08-19T12:00:00Z",
          reviewed_at: null,
        },
      ],
    }),
  );
}

test("landing page loads an example question into chat and completes a cited answer", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.goto("/");
  await page.getByRole("link", { name: /How do I configure pgvector/ }).click();
  await expect(
    page.getByRole("heading", { name: "Ask GroundStack" }),
  ).toBeVisible();
  await expect(page.getByLabel("Question")).toHaveValue(/pgvector/);
  await page.getByRole("button", { name: "Send" }).click();
  await expect(
    page.getByText("Run migrations after starting PostgreSQL"),
  ).toBeVisible();
  await page.getByRole("button", { name: "[S1]" }).click();
  await expect(
    page.getByRole("dialog", { name: "GroundStack setup" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await page.getByRole("button", { name: "Helpful" }).click();
  await expect(page.getByText("Saved")).toBeVisible();
});

test("admin product routes expose real operational states", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.goto("/sources");
  await expect(
    page.getByRole("heading", { name: "Sources and citations" }),
  ).toBeVisible();
  await page.goto("/evaluation");
  await expect(page.getByText("Demo evaluation")).toBeVisible();
  await page.goto("/training");
  await expect(page.getByText("How do I configure pgvector?")).toBeVisible();
});

test("anonymous navigation hides admin destinations", async ({ page }) => {
  await mockApi(page, "anonymous");
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Knowledge admin" })).toHaveCount(
    0,
  );
  await expect(page.getByRole("link", { name: "Evaluation" })).toHaveCount(0);
});

test("empty database states stay useful", async ({ page }) => {
  await mockApi(page, "admin");
  await page.route("**/api/v1/documents?**", (route) =>
    route.fulfill({ json: { total: 0, limit: 20, offset: 0, items: [] } }),
  );
  await page.route("**/api/v1/evaluation/runs", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.goto("/sources");
  await expect(page.getByText("No documents yet")).toBeVisible();
  await page.goto("/evaluation");
  await expect(
    page.getByRole("heading", { name: "No evaluation runs" }),
  ).toBeVisible();
});

test("mobile navigation and axe scan pass the core landing page", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(
    page.getByRole("link", { name: "Ask GroundStack" }),
  ).toBeVisible();
  const results = await new AxeBuilder({ page })
    .disableRules(["color-contrast"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("core routes do not emit browser console errors", async ({ page }) => {
  await mockApi(page, "admin");
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  for (const route of ["/", "/ask", "/sources", "/knowledge", "/evaluation"]) {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
  }
  expect(errors).toEqual([]);
});
