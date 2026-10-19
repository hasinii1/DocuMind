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
  Edit2,
  Save,
} from "lucide-react";
import {
  fetchDocuments,
  fetchExtractionSchemas,
  runExtraction,
  getExtractionCsvUrl,
} from "@/lib/api";
import { DocumentItem, ExtractionRunResult } from "@/types";

function ExtractionContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("docId") || "";

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [schemas, setSchemas] = useState<Record<string, any>>({});
  const [selectedDocId, setSelectedDocId] = useState(initialDocId);
  const [selectedSchema, setSelectedSchema] = useState("project_proposal");
  const [loading, setLoading] = useState(false);
  const [extractionResult, setExtractionResult] = useState<ExtractionRunResult | null>(null);
  const [editableData, setEditableData] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (!selectedDocId && docs.length > 0) {
          setSelectedDocId(docs[0].id);
        }
      })
      .catch(() => {});

    fetchExtractionSchemas()
      .then((s) => setSchemas(s))
      .catch(() => {});
  }, []);

  async function handleExtract(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDocId) return;

    try {
      setLoading(true);
      setError(null);
      const res = await runExtraction(selectedDocId, selectedSchema);
      setExtractionResult(res);
      setEditableData(res.extracted_data || {});
    } catch (err: any) {
      setError(err.message || "Failed to execute extraction");
    } finally {
      setLoading(false);
    }
  }

  function handleFieldChange(key: string, value: any) {
    setEditableData((prev) => ({ ...prev, [key]: value }));
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
          Extract typed, schema-defined entities (dates, monetary amounts, requirements, tabular records) into validated JSON and downloadable CSV.
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
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Extraction Schema Template
            </label>
            <select
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white text-slate-700"
            >
              {Object.entries(schemas).map(([key, schema]: [string, any]) => (
                <option key={key} value={key}>
                  {schema.title || key}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={!selectedDocId || loading}
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
                  Extraction Results: {extractionResult.schema_name}
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Review extracted values below. Missing fields are explicitly distinguished from false defaults.
              </p>
            </div>

            {/* Export Actions */}
            <div className="flex items-center space-x-2">
              <a
                href={getExtractionCsvUrl(extractionResult.id)}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </a>
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
                  <span>All required schema fields successfully extracted and verified against evidence.</span>
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
                  const isPresent = val !== null && val !== undefined;

                  return (
                    <tr key={key} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3 font-semibold text-slate-800 capitalize">
                        {key.replace(/_/g, " ")}
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={typeof val === "object" ? JSON.stringify(val) : val ?? ""}
                          onChange={(e) => handleFieldChange(key, e.target.value)}
                          placeholder="Absent in document"
                          className={`w-full max-w-sm px-2.5 py-1.5 rounded-lg border text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono ${
                            isPresent
                              ? "bg-white border-slate-200 text-slate-900"
                              : "bg-slate-50 border-dashed border-slate-300 text-slate-400 italic"
                          }`}
                        />
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {cit ? (
                          <Link
                            href={`/viewer/${extractionResult.document_id}?page=${cit.page_number}`}
                            className="inline-flex items-center space-x-1 text-brand-600 hover:underline"
                          >
                            <span>Page {cit.page_number}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </Link>
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
