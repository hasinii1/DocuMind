"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Database,
  Download,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ExternalLink,
  Plus,
  Trash2,
} from "lucide-react";
import {
  fetchDocuments,
  fetchExtractionSchemas,
  runExtraction,
} from "@/lib/api";
import {
  CustomExtractionField,
  DocumentItem,
  ExtractionRunResult,
  ExtractionSchema,
} from "@/types";

const CUSTOM_PROFILE = "__custom_profile__";

function ExtractionContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("docId") || "";

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [schemas, setSchemas] = useState<Record<string, ExtractionSchema>>({});
  const [selectedDocId, setSelectedDocId] = useState(initialDocId);
  const [selectedSchema, setSelectedSchema] = useState("universal_document");
  const [customFields, setCustomFields] = useState<CustomExtractionField[]>([]);
  const [loading, setLoading] = useState(false);
  const [extractionResult, setExtractionResult] = useState<ExtractionRunResult | null>(null);
  const [editableData, setEditableData] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const [setupError, setSetupError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (!selectedDocId && docs.length > 0) {
          setSelectedDocId(docs[0].id);
        }
      })
      .catch((err: Error) => setSetupError(`Could not load documents: ${err.message}`));

    fetchExtractionSchemas()
      .then((s) => setSchemas(s))
      .catch((err: Error) => setSetupError(`Could not load extraction templates: ${err.message}`));
  }, []);

  async function handleExtract(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDocId) return;

    try {
      setLoading(true);
      setError(null);
      const schemaName = selectedSchema === CUSTOM_PROFILE ? "universal_document" : selectedSchema;
      const baseSchema = schemas[schemaName];
      if (!baseSchema) {
        throw new Error("Extraction templates are still loading. Please try again.");
      }

      const properties = { ...baseSchema.properties };
      const required = [...(baseSchema.required || [])];
      const customKeys = new Set<string>();

      for (const field of customFields) {
        const key = field.name
          .trim()
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "_")
          .replace(/^_+|_+$/g, "");
        if (!key) {
          throw new Error("Give each custom field a name using letters or numbers.");
        }
        if (properties[key] || customKeys.has(key)) {
          throw new Error(`The field "${field.name}" duplicates an existing field.`);
        }
        customKeys.add(key);
        properties[key] = {
          type: field.type,
          title: field.name.trim(),
          description: field.description.trim(),
        };
        if (field.required) required.push(key);
      }

      const schemaWithCustomFields: ExtractionSchema = {
        ...baseSchema,
        properties,
        required,
      };
      const res = await runExtraction(
        selectedDocId,
        schemaName,
        customKeys.size ? schemaWithCustomFields : undefined
      );
      setExtractionResult(res);
      setEditableData(res.extracted_data || {});
    } catch (err: any) {
      setError(err.message || "Failed to execute extraction");
    } finally {
      setLoading(false);
    }
  }

  function handleFieldChange(key: string, value: string) {
    const fieldType = extractionResult?.target_schema.properties[key]?.type;
    let parsedValue: unknown = value;
    if (fieldType === "number" && value.trim() && !Number.isNaN(Number(value))) {
      parsedValue = Number(value);
    } else if (fieldType === "boolean" && ["true", "false"].includes(value.toLowerCase())) {
      parsedValue = value.toLowerCase() === "true";
    } else if (fieldType === "array") {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed)) parsedValue = parsed;
      } catch {
        parsedValue = value;
      }
    }
    setEditableData((prev) => ({ ...prev, [key]: parsedValue }));
  }

  function addCustomField() {
    setCustomFields((fields) => [
      ...fields,
      {
        id: Date.now() + fields.length,
        name: "",
        description: "",
        type: "string",
        required: false,
      },
    ]);
  }

  function updateCustomField(id: number, updates: Partial<CustomExtractionField>) {
    setCustomFields((fields) =>
      fields.map((field) => field.id === id ? { ...field, ...updates } : field)
    );
  }

  function downloadCsv() {
    if (!extractionResult) return;
    const escapeCell = (value: unknown) => {
      const text = typeof value === "string" ? value : JSON.stringify(value ?? "");
      const safeText = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text;
      return `"${safeText.replace(/"/g, '""')}"`;
    };
    const rows = [
      ["Field", "Value", "Status"],
      ...Object.entries(editableData).map(([key, value]) => [
        extractionResult.target_schema.properties[key]?.title || key,
        value === null || value === undefined ? "" : value,
        value === null || value === undefined ? "Absent / Missing" : "Extracted",
      ]),
    ];
    const csv = rows.map((row) => row.map(escapeCell).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `extraction_${extractionResult.schema_name}_${extractionResult.id.slice(0, 8)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadJson() {
    if (!extractionResult) return;
    const blob = new Blob([JSON.stringify(editableData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `extraction_${extractionResult.schema_name}_${extractionResult.id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Structured Data Extraction</h1>
        <p className="text-sm text-slate-500 mt-1">
          Start with a general profile for any document, or add fields that matter to your work. Results include page references where matching source text is found.
        </p>
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleExtract} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Select Document
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white text-slate-700"
            >
              <option value="">-- Select Document --</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.original_filename})
                </option>
              ))}
            </select>
            {documents.length === 0 && (
              <p className="text-xs text-slate-500">
                No documents yet. Upload a document first, then come back here.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Extraction starting point
            </label>
            <select
              value={selectedSchema}
              onChange={(e) => {
                setSelectedSchema(e.target.value);
                setExtractionResult(null);
              }}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white text-slate-700"
            >
              {Object.entries(schemas).map(([key, schema]) => (
                <option key={key} value={key}>
                  {schema.title}
                </option>
              ))}
              <option value={CUSTOM_PROFILE}>Universal profile + my fields</option>
            </select>
            <p className="text-xs text-slate-500">
              The universal profile works across document types. The other options are focused templates.
            </p>
          </div>
        </div>

        {setupError && (
          <div className="p-3 rounded-lg border border-rose-200 bg-rose-50 text-xs text-rose-700">
            Could not load extraction setup: {setupError}
          </div>
        )}

        <section className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Add your own fields</h2>
              <p className="text-xs text-slate-500">
                Optional. For example, add “Algorithm” with a description such as “definition of an algorithm”.
              </p>
            </div>
            <button
              type="button"
              onClick={addCustomField}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-brand-200 bg-white px-3 py-2 text-xs font-semibold text-brand-700 hover:bg-brand-50"
            >
              <Plus className="h-3.5 w-3.5" />
              Add field
            </button>
          </div>

          {selectedSchema === CUSTOM_PROFILE && customFields.length === 0 && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              The universal fields are always included. Add a field above to specify extra information you want to find.
            </p>
          )}

          {customFields.map((field) => (
            <div key={field.id} className="grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-3 md:grid-cols-12">
              <label className="space-y-1 text-xs font-semibold text-slate-600 md:col-span-3">
                Field name
                <input
                  value={field.name}
                  onChange={(e) => updateCustomField(field.id, { name: e.target.value })}
                  placeholder="e.g. Algorithm"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </label>
              <label className="space-y-1 text-xs font-semibold text-slate-600 md:col-span-5">
                What should we look for?
                <input
                  value={field.description}
                  onChange={(e) => updateCustomField(field.id, { description: e.target.value })}
                  placeholder="e.g. The definition or explanation of an algorithm"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </label>
              <label className="space-y-1 text-xs font-semibold text-slate-600 md:col-span-2">
                Value type
                <select
                  value={field.type}
                  onChange={(e) => updateCustomField(field.id, { type: e.target.value as CustomExtractionField["type"] })}
                  className="w-full rounded-lg border border-slate-200 bg-white px-2 py-2 text-sm font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="string">Text</option>
                  <option value="array">List</option>
                  <option value="number">Number</option>
                  <option value="boolean">Yes / No</option>
                </select>
              </label>
              <div className="flex items-end justify-between gap-2 md:col-span-2">
                <label className="flex items-center gap-1.5 pb-2 text-xs text-slate-600">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(e) => updateCustomField(field.id, { required: e.target.checked })}
                    className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  Required
                </label>
                <button
                  type="button"
                  onClick={() => setCustomFields((fields) => fields.filter((item) => item.id !== field.id))}
                  aria-label={`Remove ${field.name || "custom"} field`}
                  className="mb-1 rounded p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
          <p className="text-[11px] leading-relaxed text-slate-500">
            Extraction uses document text and section headings to find relevant passages. It does not invent missing values; check the linked page before relying on a result.
          </p>
        </section>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={!selectedDocId || loading || Object.keys(schemas).length === 0}
          className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold py-2.5 px-5 rounded-xl text-sm transition-all shadow-sm flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Scanning document & validating schema fields...</span>
            </>
          ) : (
            <>
              <Database className="w-4 h-4" />
              <span>Extract Schema Fields</span>
            </>
          )}
        </button>
      </form>

      {/* Extraction Results Table */}
      {extractionResult && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h2 className="font-bold text-slate-900 text-base">
                  Extraction Results: {extractionResult.schema_title || extractionResult.schema_name}
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Review extracted values below. Missing fields are explicitly distinguished from false defaults.
              </p>
            </div>

            {/* Export Actions */}
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={downloadCsv}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={downloadJson}
                className="bg-brand-600 hover:bg-brand-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export JSON</span>
              </button>
            </div>
          </div>

          {/* Validation Banner */}
          {extractionResult.validation && (
            <div
              className={`p-3 rounded-xl text-xs flex items-center space-x-2 ${
                extractionResult.validation.is_valid
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-amber-50 text-amber-800 border border-amber-200"
              }`}
            >
              {extractionResult.validation.is_valid ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>All required fields have a value. Check each source-page citation before relying on the result.</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>
                    Missing required fields: {extractionResult.validation.missing_required.join(", ")}
                  </span>
                </>
              )}
            </div>
          )}

          {/* Editable Field Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Schema Field</th>
                  <th className="px-4 py-3 text-left">Extracted Value (Editable)</th>
                  <th className="px-4 py-3 text-left">Source Citation</th>
                  <th className="px-4 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Object.entries(editableData).map(([key, val]) => {
                  const cit = extractionResult.field_citations?.[key];
                  const sourceCitations = cit ? (Array.isArray(cit) ? cit : [cit]) : [];
                  const isPresent = val !== null && val !== undefined;

                  return (
                    <tr key={key} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3 font-semibold text-slate-800 capitalize">
                          {extractionResult.target_schema.properties[key]?.title || key.replace(/_/g, " ")}
                      </td>
                      <td className="px-4 py-3">
                        <textarea
                          value={typeof val === "object" && val !== null ? JSON.stringify(val, null, 2) : String(val ?? "")}
                          onChange={(e) => handleFieldChange(key, e.target.value)}
                          placeholder="Absent in document"
                          rows={typeof val === "object" && val !== null ? 4 : 2}
                          className={`w-full max-w-sm px-2.5 py-1.5 rounded-lg border text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono ${
                            isPresent
                              ? "bg-white border-slate-200 text-slate-900"
                              : "bg-slate-50 border-dashed border-slate-300 text-slate-400 italic"
                          }`}
                        />
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {sourceCitations.length ? (
                          <div className="flex max-w-40 flex-wrap gap-2">
                            {sourceCitations.map((source, index) => (
                              <Link
                                key={`${source.chunk_id}-${index}`}
                                href={`/viewer/${extractionResult.document_id}?page=${source.page_number}`}
                                title={source.quote}
                                className="inline-flex items-center gap-1 text-brand-600 hover:underline"
                              >
                                <span>Page {source.page_number}</span>
                                <ExternalLink className="h-2.5 w-2.5" />
                              </Link>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            isPresent
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-slate-100 text-slate-500 border border-slate-200"
                          }`}
                        >
                          {isPresent ? "Extracted" : "Absent"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ExtractionPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading Extraction Engine...</div>}>
      <ExtractionContent />
    </Suspense>
  );
}
