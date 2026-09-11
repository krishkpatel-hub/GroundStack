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
  await page.route(`**/api/v1/documents/${documentId}`, (route) =>
    route.fulfill({
      status: route.request().method() === "DELETE" ? 204 : 200,
      body: "",
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
}

test("landing page opens the workspace and completes a cited answer", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Ask technical questions. Get answers backed by your documentation.",
    }),
  ).toBeVisible();
  await page
    .getByRole("main")
    .getByRole("link", { name: "Open workspace" })
    .click();
  await expect(page.getByRole("heading", { name: "Workspace" })).toBeVisible();
  await page
    .getByLabel("Question")
    .fill("How do I configure pgvector for GroundStack?");
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

test("admin core routes expose source and document-management states", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.goto("/ask");
  await expect(
    page.getByLabel("Workspace views").getByRole("tab", { name: "Ask" }),
  ).toHaveAttribute("aria-current", "page");
  await page
    .getByLabel("Workspace views")
    .getByRole("tab", { name: "Documents" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Knowledge base" }),
  ).toBeVisible();
  await expect(page.getByText("Maximum file size: 10 MB")).toBeVisible();
  await page.getByRole("button", { name: "Delete" }).click();
  await expect(
    page.getByRole("dialog", { name: "Delete document?" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel" }).click();
});

test("anonymous navigation hides admin destinations", async ({ page }) => {
  await mockApi(page, "anonymous");
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Evaluation" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Training" })).toHaveCount(0);
});

test("empty database states stay useful", async ({ page }) => {
  await mockApi(page, "admin");
  await page.route("**/api/v1/documents?**", (route) =>
    route.fulfill({ json: { total: 0, limit: 20, offset: 0, items: [] } }),
  );
  await page.goto("/knowledge");
  await expect(page.getByText("No documents yet")).toBeVisible();
  await page.goto("/ask");
  await expect(
    page.getByRole("heading", {
      name: "Add a document before asking",
    }),
  ).toBeVisible();
  await expect(page.getByLabel("Question")).toBeDisabled();
});

test("api connectivity errors are written for users instead of hidden", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.route("**/api/v1/documents?**", (route) => route.abort("failed"));
  await page.goto("/ask");
  await expect(
    page.getByText("GroundStack cannot reach the API"),
  ).toBeVisible();
});

test("mobile navigation and axe scan pass the core landing page", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("link", { name: "Open workspace" }).first().click();
  await expect(
    page.getByLabel("Workspace views").getByRole("tab", { name: "Documents" }),
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
  for (const route of ["/", "/ask", "/sources", "/knowledge", "/about"]) {
    await page.goto(route);
    await page.getByRole("main").waitFor({ state: "visible" });
  }
  expect(errors).toEqual([]);
});
