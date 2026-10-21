"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  GitCompare,
  ArrowRight,
  Loader2,
  FileText,
  AlertTriangle,
  PlusCircle,
  MinusCircle,
  RefreshCw,
  ExternalLink,
  UploadCloud,
  CheckCircle2,
} from "lucide-react";
import { fetchDocuments, compareDocuments, uploadDocument } from "@/lib/api";
import { DocumentItem, ComparisonResult } from "@/types";

export default function CompareDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [baseDocId, setBaseDocId] = useState("");
  const [targetDocId, setTargetDocId] = useState("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [baseFile, setBaseFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [uploadingVersion, setUploadingVersion] = useState<"base" | "target" | null>(null);

  useEffect(() => {
    async function loadInitialDocuments() {
      try {
        const docs = await fetchDocuments();
        setDocuments(docs);
        if (docs.length > 0) setTargetDocId(docs[0].id);
        if (docs.length > 1) setBaseDocId(docs[1].id);
      } catch (err) {
        setDocumentsError(err instanceof Error ? err.message : "Could not load your document library.");
      }
    }
    void loadInitialDocuments();
  }, []);

  async function refreshDocuments() {
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
      setDocumentsError(null);
    } catch (err) {
      setDocumentsError(err instanceof Error ? err.message : "Could not load your document library.");
    }
  }

  async function handleVersionUpload(side: "base" | "target") {
    const file = side === "base" ? baseFile : targetFile;
    if (!file) return;

    try {
      setUploadingVersion(side);
      setError(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", file.name.replace(/\.[^/.]+$/, ""));
      formData.append("workspace_id", "default-workspace");
      const result = await uploadDocument(formData);
      const uploadedId = result.document_id || result.document?.id;
      if (!uploadedId) {
        throw new Error("The upload finished without returning a document ID.");
      }
      if (side === "base") {
        setBaseDocId(uploadedId);
        setBaseFile(null);
      } else {
        setTargetDocId(uploadedId);
        setTargetFile(null);
      }
      await refreshDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload document.");
    } finally {
      setUploadingVersion(null);
    }
  }

  async function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    if (!baseDocId || !targetDocId) return;
    if (baseDocId === targetDocId) {
      setError("Please select two distinct document versions to compare.");
      return;
    }
    if (documents.some((doc) =>
      (doc.id === baseDocId || doc.id === targetDocId) && doc.processing_status !== "completed"
    )) {
      setError("Both documents must finish processing before they can be compared.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await compareDocuments(baseDocId, targetDocId);
      setComparison(res);
    } catch (err: any) {
      setError(err.message || "Failed to execute comparison.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Compare Document Versions</h1>
        <p className="text-sm text-slate-500 mt-1">
          Choose two processed documents from your library or upload the original and revised PDF files here.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2" aria-label="Upload versions to compare">
        {([
          { side: "base" as const, title: "Original version", file: baseFile, setFile: setBaseFile },
          { side: "target" as const, title: "Revised version", file: targetFile, setFile: setTargetFile },
        ]).map(({ side, title, file, setFile }) => (
          <div key={side} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <span className="rounded-lg bg-brand-50 p-2 text-brand-700"><UploadCloud className="h-4 w-4" /></span>
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Upload {title.toLowerCase()}</h2>
                <p className="text-xs text-slate-500">PDF files are added to your library</p>
              </div>
            </div>
            <input
              type="file"
              accept=".pdf,application/pdf"
              aria-label={`Choose ${title.toLowerCase()} PDF`}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-brand-700 hover:file:bg-brand-100"
            />
            {file && (
              <div className="mt-3 flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2">
                <span className="truncate text-xs text-slate-600">{file.name}</span>
                <button
                  type="button"
                  disabled={uploadingVersion !== null}
                  onClick={() => void handleVersionUpload(side)}
                  className="shrink-0 rounded-lg bg-brand-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-800 disabled:opacity-50"
                >
                  {uploadingVersion === side ? "Uploading..." : "Add version"}
                </button>
              </div>
            )}
          </div>
        ))}
      </section>

      <p className="rounded-xl border border-brand-100 bg-brand-50/70 px-4 py-3 text-xs leading-5 text-brand-900">
        Uploading stores each file in your library and starts text extraction. You can compare it once its status is <strong>completed</strong>.
        Comparison highlights text additions, removals, and modifications; review important changes against the linked source pages.
      </p>

      {/* Version Selector Form */}
      <form onSubmit={handleCompare} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Choose versions from your library</h2>
            <p className="mt-1 text-xs text-slate-500">Only fully processed documents can be compared.</p>
          </div>
          <button
            type="button"
            onClick={() => void refreshDocuments()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>
        {documentsError && <p role="alert" className="text-xs text-rose-700">{documentsError}</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Base Version (Original)
            </label>
            <select
              value={baseDocId}
              onChange={(e) => setBaseDocId(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            >
              <option value="">-- Select Base Document --</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id} disabled={d.processing_status !== "completed"}>
                  {d.title} ({d.processing_status === "completed" ? `${d.page_count} pages` : d.processing_status})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Revised Version (Target)
            </label>
            <select
              value={targetDocId}
              onChange={(e) => setTargetDocId(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
            >
              <option value="">-- Select Revised Document --</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id} disabled={d.processing_status !== "completed"}>
                  {d.title} ({d.processing_status === "completed" ? `${d.page_count} pages` : d.processing_status})
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

        {baseDocId && targetDocId && baseDocId !== targetDocId &&
          documents.find((doc) => doc.id === baseDocId)?.processing_status === "completed" &&
          documents.find((doc) => doc.id === targetDocId)?.processing_status === "completed" && (
            <p className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
              <CheckCircle2 className="h-4 w-4" /> Both versions are ready to compare.
            </p>
          )}

        <button
          type="submit"
          disabled={!baseDocId || !targetDocId || loading ||
            documents.find((doc) => doc.id === baseDocId)?.processing_status !== "completed" ||
            documents.find((doc) => doc.id === targetDocId)?.processing_status !== "completed"}
          className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold py-2.5 px-5 rounded-xl text-sm transition-all shadow-sm flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Aligning sections & classifying diffs...</span>
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4" />
              <span>Compare Versions</span>
            </>
          )}
        </button>
      </form>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-5">
          {/* Summary & Statistics Bar */}
          <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <span className="font-bold text-sm text-brand-300">Comparison Summary</span>
              {comparison.statistics && (
                <div className="flex items-center space-x-3 text-xs">
                  <span className="text-emerald-400 font-semibold">
                    +{comparison.statistics.additions} Additions
                  </span>
                  <span className="text-rose-400 font-semibold">
                    -{comparison.statistics.deletions} Deletions
                  </span>
                  <span className="text-brand-300 font-semibold">
                    ~{comparison.statistics.modifications} Modifications
                  </span>
                  <span className="text-amber-400 font-bold">
                    ! {comparison.statistics.critical} Critical Shifts
                  </span>
                </div>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-mono">
              {comparison.summary}
            </p>
          </div>

          {/* Detailed Changes List */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
              Aligned Changes ({comparison.changes.length})
            </h2>

            {comparison.changes.map((change, idx) => (
              <div
                key={idx}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {change.change_type === "addition" && (
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                        <PlusCircle className="w-3.5 h-3.5" />
                        <span>Added Section</span>
                      </span>
                    )}
                    {change.change_type === "deletion" && (
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-0.5 rounded-full">
                        <MinusCircle className="w-3.5 h-3.5" />
                        <span>Removed Clause</span>
                      </span>
                    )}
                    {change.change_type === "modification" && (
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-brand-700 bg-brand-50 border border-brand-200 px-2.5 py-0.5 rounded-full">
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Modified Text</span>
                      </span>
                    )}

                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        change.significance === "critical"
                          ? "bg-rose-100 text-rose-800 border border-rose-300"
                          : change.significance === "high"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {change.significance.toUpperCase()} IMPACT
                    </span>
                  </div>

                  <span className="text-xs text-slate-500 font-medium">
                    {change.section_title || "General Section"}
                  </span>
                </div>

                <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <strong className="text-slate-800">Classification Rationale:</strong> {change.explanation}
                </p>

                {/* Diff Side-by-Side Content */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  {change.old_text && (
                    <div className="p-3 bg-rose-50/50 border border-rose-100 rounded-xl space-y-1">
                      <div className="flex justify-between items-center text-[10px] text-rose-700 font-sans font-bold">
                        <span>Base Version (Page {change.old_page || 1})</span>
                        {baseDocId && (
                          <Link
                            href={`/viewer/${baseDocId}?page=${change.old_page || 1}`}
                            className="hover:underline inline-flex items-center space-x-0.5"
                          >
                            <span>Verify</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </Link>
                        )}
                      </div>
                      <p className="text-rose-900 whitespace-pre-wrap">{change.old_text}</p>
                    </div>
                  )}

                  {change.new_text && (
                    <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl space-y-1">
                      <div className="flex justify-between items-center text-[10px] text-emerald-700 font-sans font-bold">
                        <span>Revised Version (Page {change.new_page || 1})</span>
                        {targetDocId && (
                          <Link
                            href={`/viewer/${targetDocId}?page=${change.new_page || 1}`}
                            className="hover:underline inline-flex items-center space-x-0.5"
                          >
                            <span>Verify</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </Link>
                        )}
                      </div>
                      <p className="text-emerald-900 whitespace-pre-wrap">{change.new_text}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
