export type RetrievalFilters = {
  source_types?: string[];
  source_ids?: string[];
  document_ids?: string[];
};

export type Citation = {
  citation_id: string;
  source_id: string;
  document_id: string;
  document_version: number;
  chunk_id: string;
  title: string;
  source_display_name: string;
  source_type: string;
  source_uri: string | null;
  section_path: string | null;
  page_number: number | null;
  excerpt: string;
  final_rank: number;
};
