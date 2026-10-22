import type { ExtractionRunResult, ExtractionSchema } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchDocuments(workspaceId = "default-workspace") {
  const res = await fetch(`${API_BASE}/documents?workspace_id=${workspaceId}`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function fetchDocument(documentId: string) {
  const res = await fetch(`${API_BASE}/documents/${documentId}`);
  if (!res.ok) throw new Error("Failed to fetch document");
  return res.json();
}

export async function fetchPageElements(documentId: string, pageNumber: number) {
  const res = await fetch(`${API_BASE}/documents/${documentId}/pages/${pageNumber}`);
  if (!res.ok) throw new Error("Failed to fetch page elements");
  return res.json();
}

export async function uploadDocument(formData: FormData) {
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || "Upload failed");
  }
  return res.json();
}

export async function deleteDocument(documentId: string) {
  const res = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}

export async function createConversation(title = "New Conversation", workspaceId = "default-workspace") {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, workspace_id: workspaceId }),
  });
  if (!res.ok) throw new Error("Failed to create conversation");
  return res.json();
}

export async function fetchConversations(workspaceId = "default-workspace") {
  const res = await fetch(`${API_BASE}/conversations?workspace_id=${workspaceId}`);
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json();
}

export async function fetchConversationMessages(conversationId: string) {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`);
  if (!res.ok) throw new Error("Failed to fetch conversation history");
  return res.json();
}

export async function clearConversationMessages(conversationId: string) {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to clear conversation");
  return res.json();
}

export async function deleteConversation(conversationId: string) {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
  return res.json();
}

export async function askQuestion(conversationId: string, question: string, documentIds?: string[]) {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_ids: documentIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to send question" }));
    throw new Error(err.detail || "Failed to send question");
  }
  return res.json();
}

export async function compareDocuments(baseDocId: string, targetDocId: string, workspaceId = "default-workspace") {
  const res = await fetch(`${API_BASE}/comparisons`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base_document_id: baseDocId,
      target_document_id: targetDocId,
      workspace_id: workspaceId,
    }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to compare documents" }));
    throw new Error(error.detail || "Failed to compare documents");
  }
  return res.json();
}

export async function fetchExtractionSchemas(): Promise<Record<string, ExtractionSchema>> {
  const res = await fetch(`${API_BASE}/extractions/schemas`);
  if (!res.ok) throw new Error("Failed to fetch extraction schemas");
  return res.json();
}

export async function runExtraction(
  documentId: string,
  schemaName = "project_proposal",
  customSchema?: ExtractionSchema
): Promise<ExtractionRunResult> {
  const res = await fetch(`${API_BASE}/extractions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      schema_name: schemaName,
      custom_schema: customSchema,
    }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to run extraction" }));
    throw new Error(error.detail || "Failed to run extraction");
  }
  return res.json();
}

export function getDocumentDownloadUrl(documentId: string): string {
  return `${API_BASE}/documents/${documentId}/download`;
}

export function getExtractionCsvUrl(extractionId: string): string {
  return `${API_BASE}/extractions/${extractionId}/export/csv`;
}
