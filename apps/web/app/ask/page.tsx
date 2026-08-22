import { AppShell } from "@/components/app-shell";

export default function AskPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  return <AskPageContent searchParams={searchParams} />;
}

async function AskPageContent({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const params = await searchParams;
  return <AppShell initialQuestion={params.q ?? ""} />;
}
