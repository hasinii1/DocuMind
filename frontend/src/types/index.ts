export interface DocumentItem {
  id: string;
  title: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number;
  has_tables: boolean;
  has_scanned_pages: boolean;
  processing_status: "pending" | "processing" | "completed" | "failed";
  parent_document_id?: string | null;
  error_message?: string | null;
  created_at?: string;
  chunk_count?: number;
  element_count?: number;
}

export interface DocumentElement {
  id: string;
  element_type: "paragraph" | "heading" | "table" | "figure" | "ocr_text";
  content: string;
  bounding_box?: { x0: number; y0: number; x1: number; y1: number } | null;
  source_method: string;
  metadata?: any;
}

export interface Citation {
  id?: string;
  chunk_id: string;
  document_id: string;
  document_title?: string;
  page_number: number;
  page_end?: number;
  section_title?: string;
  quote: string;
  is_verified: boolean;
  confidence_score: number;
}

export interface RetrievedEvidence {
  chunk_id: string;
  document_id: string;
  page_start: number;
  page_end: number;
  section_title?: string;
  element_type: string;
  content: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  insufficient_evidence?: boolean;
  citations?: Citation[];
  retrieved_evidence?: RetrievedEvidence[];
  security_warning?: boolean;
  created_at?: string;
}

export interface ComparisonChange {
  change_type: "addition" | "deletion" | "modification";
  significance: "critical" | "high" | "medium" | "low";
  explanation: string;
  old_page?: number | null;
  new_page?: number | null;
  section_title?: string | null;
  old_text: string;
  new_text: string;
  old_chunk_id?: string | null;
  new_chunk_id?: string | null;
}

export interface ComparisonResult {
  id: string;
  base_document?: { id: string; title: string };
  target_document?: { id: string; title: string };
  summary: string;
  statistics?: {
    additions: number;
    deletions: number;
    modifications: number;
    critical: number;
  };
  changes: ComparisonChange[];
}

export interface ExtractionSchemaField {
  type: "string" | "number" | "array" | "boolean";
  title?: string;
  description?: string;
}

export interface ExtractionSchema {
  title: string;
  description: string;
  properties: Record<string, ExtractionSchemaField>;
  required?: string[];
}

export interface CustomExtractionField {
  id: number;
  name: string;
  description: string;
  type: ExtractionSchemaField["type"];
  required: boolean;
}

export interface ExtractionCitation {
  chunk_id: string;
  page_number: number;
  quote: string;
}

export interface ExtractionRunResult {
  id: string;
  document_id: string;
  document_title?: string;
  schema_name: string;
  schema_title?: string;
  target_schema: ExtractionSchema;
  extracted_data: Record<string, unknown>;
  field_citations?: Record<string, ExtractionCitation | ExtractionCitation[]>;
  validation?: {
    is_valid: boolean;
    missing_required: string[];
  };
  review_status: "draft" | "reviewed" | "approved";
}
