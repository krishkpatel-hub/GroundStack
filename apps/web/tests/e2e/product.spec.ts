import { AxeBuilder } from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const conversationId = "11111111-1111-1111-1111-111111111111";
const messageId = "22222222-2222-2222-2222-222222222222";
const documentId = "33333333-3333-3333-3333-333333333333";

async function mockApi(
  page: Page,
  role: "anonymous" | "admin" = "admin",
  options: { onChatStream?: () => void; failGeneration?: boolean } = {},
) {
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
          title: "Demo: DB-104 support",
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
            content: "What does DB-104 mean?",
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
        total: 10,
        limit: 20,
        offset: 0,
        items: [
          {
            id: documentId,
            source_id: "44444444-4444-4444-4444-444444444444",
            source_type: "file",
            display_name: "04-db-104.md",
            source_status: "active",
            version: 1,
            title: "Northstar Systems Database Error DB-104",
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
            heading_path: ["Meaning"],
            content:
              "DB-104 means the application connected to the database host but failed the schema readiness check.",
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
  await page.route("**/api/v1/chat/stream", async (route) => {
    options.onChatStream?.();
    const body = route.request().postDataJSON() as { question?: string };
    const unsupported = body.question?.includes("parental-leave");
    const citationEvent = `event: retrieval_completed\ndata: {"citations":[{"citation_id":"S1","source_id":"44444444-4444-4444-4444-444444444444","document_id":"${documentId}","document_version":1,"chunk_id":"55555555-5555-5555-5555-555555555555","title":"Northstar Systems Database Error DB-104","source_display_name":"04-db-104.md","source_type":"file","source_uri":null,"section_path":"Meaning","page_number":null,"excerpt":"DB-104 means the application connected to the database host but failed the schema readiness check.","final_rank":1}]}\n\n`;
    return route.fulfill({
      headers: { "content-type": "text/event-stream" },
      body: [
        `event: conversation\ndata: {"conversation_id":"${conversationId}"}\n\n`,
        unsupported
          ? `event: retrieval_completed\ndata: {"citations":[]}\n\n`
          : citationEvent,
        ...(unsupported
          ? [
              `event: canonical_answer\ndata: {"message_id":"${messageId}","answer":"I do not have enough retrieved evidence to answer this question. Add or select relevant documentation in the Knowledge Base, then search again.","grounding_status":"insufficient_evidence"}\n\n`,
              `event: completed\ndata: {}\n\n`,
            ]
          : options.failGeneration
            ? [
                `event: generation_started\ndata: {}\n\n`,
                `event: error\ndata: {"message":"fake http_500","grounding_status":"generation_failed"}\n\n`,
              ]
            : [
                `event: generation_started\ndata: {}\n\n`,
                `event: token\ndata: {"token":"DB-104 means the application reached the database but failed the schema readiness check. Run migration status, apply pending migrations with the change ticket, restart the service, and confirm schema_ready=true. [S1]"}\n\n`,
                `event: canonical_answer\ndata: {"message_id":"${messageId}","answer":"DB-104 means the application reached the database but failed the schema readiness check. Run migration status, apply pending migrations with the change ticket, restart the service, and confirm schema_ready=true. [S1]","grounding_status":"grounded"}\n\n`,
                `event: completed\ndata: {}\n\n`,
              ]),
      ].join(""),
    });
  });
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
      name: "A private technical-support assistant for approved documentation.",
    }),
  ).toBeVisible();
  await expect(page.getByText("Northstar Systems is fictional")).toBeVisible();
  const workspaceLink = page
    .getByRole("main")
    .getByRole("link", { name: "Open workspace" });
  await expect(workspaceLink).toHaveAttribute("href", "/ask");
  await page.goto("/ask");
  await expect(page.getByRole("heading", { name: "Workspace" })).toBeVisible();
  await expect(
    page.getByText("Fictional demo workspace", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "What does DB-104 mean, and how should I resolve it?",
    })
    .click();
  await page
    .getByRole("textbox", { name: "Question" })
    .fill("What does DB-104 mean, and how should I resolve it?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("schema readiness check")).toBeVisible();
  await page.getByRole("button", { name: "[S1]" }).click();
  await expect(
    page.getByRole("dialog", { name: "Source evidence" }),
  ).toBeVisible();
  await expect(
    page.getByText("Northstar Systems Database Error DB-104"),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await page.getByRole("button", { name: "Helpful" }).click();
  await expect(page.getByText("Saved")).toBeVisible();
});

test("chat submission is guarded against rapid duplicate sends", async ({
  page,
}) => {
  let chatRequests = 0;
  await mockApi(page, "admin", {
    onChatStream: () => {
      chatRequests += 1;
    },
  });
  await page.goto("/ask");
  await page
    .getByLabel("Example questions")
    .getByRole("button", {
      name: "What does DB-104 mean, and how should I resolve it?",
    })
    .click();
  const send = page.getByRole("button", { name: "Send" });
  await Promise.all([send.dispatchEvent("click"), send.dispatchEvent("click")]);
  await expect(page.getByText("schema readiness check")).toBeVisible();
  expect(chatRequests).toBe(1);
});

test("provider failure does not render raw errors as cited answers", async ({
  page,
}) => {
  await mockApi(page, "admin", { failGeneration: true });
  await page.goto("/ask");
  await page
    .getByLabel("Example questions")
    .getByRole("button", {
      name: "What does DB-104 mean, and how should I resolve it?",
    })
    .click();
  await page.getByRole("button", { name: "Send" }).click();
  await expect(
    page
      .getByText(
        "GroundStack could not generate an answer. Retry after the provider recovers.",
      )
      .first(),
  ).toBeVisible();
  await expect(page.getByText("fake http_500")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "[S1]" })).toHaveCount(0);
  await expect(
    page.getByText("Generation failed", { exact: true }),
  ).toBeVisible();
});

test("northstar unsupported question returns insufficient evidence", async ({
  page,
}) => {
  await mockApi(page, "admin");
  await page.goto("/ask");
  await page
    .getByRole("button", {
      name: "What is Northstar Systems' parental-leave policy?",
    })
    .click();
  await page.getByRole("button", { name: "Send" }).click();
  await expect(
    page.getByText("I do not have enough retrieved evidence"),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "[S1]" })).toHaveCount(0);
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
  await expect(
    page.getByText("Northstar Systems support corpus"),
  ).toBeVisible();
  await expect(page.getByText("Maximum file size: 10 MB")).toBeVisible();
  await page.getByRole("button", { name: "Delete" }).click();
  await expect(
    page.getByRole("dialog", { name: "Delete document?" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel" }).click();
});

test("document upload rejects unsupported file types before submission", async ({
  page,
}) => {
  let uploadRequests = 0;
  await mockApi(page, "admin");
  await page.route("**/api/v1/ingestions/files", (route) => {
    uploadRequests += 1;
    return route.fulfill({
      json: { job_id: "job", status: "queued" },
    });
  });
  await page.goto("/knowledge");
  await page.locator('input[type="file"]').setInputFiles({
    name: "policy.docx",
    mimeType:
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    buffer: Buffer.from("not supported"),
  });
  await expect(
    page.getByText("policy.docx is not a supported document type"),
  ).toBeVisible();
  expect(uploadRequests).toBe(0);
});

test("anonymous navigation hides admin destinations", async ({ page }) => {
  await mockApi(page, "anonymous");
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Evaluation" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Training" })).toHaveCount(0);
  await page.goto("/ask");
  await expect(
    page.getByLabel("Workspace views").getByRole("tab", { name: "Documents" }),
  ).toHaveCount(0);
  await page.goto("/knowledge");
  await expect(page.getByText("Admin access required")).toBeVisible();
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
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

test("core workspace routes avoid horizontal overflow at reviewed widths", async ({
  page,
}) => {
  await mockApi(page, "admin");
  for (const width of [320, 375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["/", "/ask", "/knowledge", "/sources"]) {
      await page.goto(route);
      await page.getByRole("main").waitFor({ state: "visible" });
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);
    }
  }
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
