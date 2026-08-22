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
          title: "Demo: pgvector setup",
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
        `event: token\ndata: {"token":"Run migrations after starting PostgreSQL with pgvector. [S1]"}\n\n`,
        `event: canonical_answer\ndata: {"message_id":"${messageId}","answer":"Run migrations after starting PostgreSQL with pgvector. [S1]","grounding_status":"grounded"}\n\n`,
        `event: completed\ndata: {}\n\n`,
      ].join(""),
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
}

test("capture portfolio screenshots", async ({ page }) => {
  await mockScreens(page);
  await page.goto("/");
  await page.screenshot({ path: `${out}/landing.png`, fullPage: true });
  await page.goto("/ask?q=How%20do%20I%20configure%20pgvector%3F");
  await page.getByRole("button", { name: "Send" }).click();
  await page.getByText("Run migrations after starting PostgreSQL").waitFor();
  await page.screenshot({
    path: `${out}/chat-with-citations.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "[S1]" }).click();
  await page.screenshot({ path: `${out}/source-viewer.png`, fullPage: true });
  await page.goto("/knowledge");
  await page.screenshot({ path: `${out}/knowledge-admin.png`, fullPage: true });
  await page.goto("/evaluation");
  await page.getByText("Demo evaluation").waitFor();
  await page.screenshot({
    path: `${out}/evaluation-comparison.png`,
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/ask?q=How%20do%20I%20configure%20pgvector%3F");
  await page.screenshot({ path: `${out}/mobile-chat.png`, fullPage: true });
});
