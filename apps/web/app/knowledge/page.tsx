import { KnowledgeBase } from "@/components/knowledge/knowledge-base";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Workspace",
  robots: {
    index: false,
    follow: false,
  },
};

export default function KnowledgePage() {
  return <KnowledgeBase />;
}
