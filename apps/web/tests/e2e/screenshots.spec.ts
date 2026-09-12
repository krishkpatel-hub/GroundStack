import { test, type Page } from "@playwright/test";

const out = "../../docs/assets/screenshots";
const conversationId = "11111111-1111-1111-1111-111111111111";
const messageId = "22222222-2222-2222-2222-222222222222";
const documentId = "33333333-3333-3333-3333-333333333333";

async function mockScreens(page: Page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      json: {
        authenticated: true,
        anonymous: false,
        subject: "admin",
        roles: ["admin"],
        admin: true,
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
  await page.route("**/api/v1/chat/stream", (route) =>
    route.fulfill({
      headers: { "content-type": "text/event-stream" },
      body: [
        `event: conversation\ndata: {"conversation_id":"${conversationId}"}\n\n`,
        `event: retrieval_completed\ndata: {"citations":[{"citation_id":"S1","source_id":"44444444-4444-4444-4444-444444444444","document_id":"${documentId}","document_version":1,"chunk_id":"55555555-5555-5555-5555-555555555555","title":"Northstar Systems Database Error DB-104","source_display_name":"04-db-104.md","source_type":"file","source_uri":null,"section_path":"Meaning","page_number":null,"excerpt":"DB-104 means the application connected to the database host but failed the schema readiness check.","final_rank":1}]}\n\n`,
        `event: token\ndata: {"token":"DB-104 means the application reached the database but failed the schema readiness check. Run migration status, apply pending migrations with the change ticket, restart the service, and confirm schema_ready=true. [S1]"}\n\n`,
        `event: canonical_answer\ndata: {"message_id":"${messageId}","answer":"DB-104 means the application reached the database but failed the schema readiness check. Run migration status, apply pending migrations with the change ticket, restart the service, and confirm schema_ready=true. [S1]","grounding_status":"grounded"}\n\n`,
        `event: completed\ndata: {}\n\n`,
      ].join(""),
    }),
  );
}

async function captureAppScreenshot(page: Page, path: string) {
  await page.evaluate(() => {
    document
      .querySelectorAll(
        "nextjs-portal, [data-nextjs-devtools], [data-nextjs-dialog-overlay]",
      )
      .forEach((element) => element.remove());
  });
  await page.screenshot({ path, fullPage: true });
}

test("capture portfolio screenshots", async ({ page }) => {
  test.skip(
    test.info().project.name !== "chromium-desktop",
    "Portfolio screenshots are captured once from the desktop Chromium project.",
  );
  await mockScreens(page);
  await page.goto("/");
  await captureAppScreenshot(page, `${out}/landing.png`);
  await page.goto("/ask?q=What%20does%20DB-104%20mean%3F");
  await page.getByRole("button", { name: "Send" }).click();
  await page.getByText("schema readiness check").waitFor();
  await captureAppScreenshot(page, `${out}/chat-with-citations.png`);
  await page.getByRole("button", { name: "[S1]" }).click();
  await captureAppScreenshot(page, `${out}/source-viewer.png`);
  await page.goto("/knowledge");
  await captureAppScreenshot(page, `${out}/knowledge-admin.png`);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ask?q=What%20does%20DB-104%20mean%3F");
  await captureAppScreenshot(page, `${out}/mobile-chat.png`);
});
