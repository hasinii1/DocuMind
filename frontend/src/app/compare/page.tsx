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
} from "lucide-react";
import { fetchDocuments, compareDocuments } from "@/lib/api";
import { DocumentItem, ComparisonResult } from "@/types";

export default function CompareDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [baseDocId, setBaseDocId] = useState("");
  const [targetDocId, setTargetDocId] = useState("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments()
      .then((docs) => {
        setDocuments(docs);
        if (docs.length >= 2) {
          setBaseDocId(docs[0].id);
          setTargetDocId(docs[1].id);
        }
      })
      .catch(() => {});
  }, []);

  async function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    if (!baseDocId || !targetDocId) return;
    if (baseDocId === targetDocId) {
      setError("Please select two distinct document versions to compare.");
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
          Perform semantic version diffing between two documents to identify additions, removals, changed clauses, and altered numerical values.
        </p>
      </div>

      {/* Version Selector Form */}
      <form onSubmit={handleCompare} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
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
                <option key={d.id} value={d.id}>
                  {d.title} ({d.page_count} pages)
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
                <option key={d.id} value={d.id}>
                  {d.title} ({d.page_count} pages)
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
          disabled={!baseDocId || !targetDocId || loading}
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
                  <span className="text-blue-400 font-semibold">
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
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full">
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
