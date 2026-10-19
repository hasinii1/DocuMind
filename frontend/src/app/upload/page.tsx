"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileCheck,
  AlertCircle,
  Loader2,
  ArrowRight,
  ShieldAlert,
  GitBranch,
} from "lucide-react";
import { uploadDocument, fetchDocuments } from "@/lib/api";
import { DocumentItem } from "@/types";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [parentDocId, setParentDocId] = useState("");
  const [existingDocs, setExistingDocs] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progressStage, setProgressStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successDocId, setSuccessDocId] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments()
      .then((docs) => setExistingDocs(docs))
      .catch(() => {});
  }, []);

  function handleFileDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      setFile(dropped);
      if (!title) setTitle(dropped.name.replace(/\.[^/.]+$/, ""));
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      if (!title) setTitle(selected.name.replace(/\.[^/.]+$/, ""));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      setProgressStage("Uploading document & verifying checksum...");

      const formData = new FormData();
      formData.append("file", file);
      if (title) formData.append("title", title);
      if (parentDocId) formData.append("parent_document_id", parentDocId);
      formData.append("workspace_id", "default-workspace");

      const res = await uploadDocument(formData);
      setSuccessDocId(res.document_id || res.document?.id);
      setProgressStage("Document ingested & embeddings generated!");
    } catch (err: any) {
      setError(err.message || "Upload and processing failed.");
      setProgressStage(null);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Upload & Process Document</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload PDFs, scanned documents, or reports for layout-aware parsing, table extraction, and vector indexing.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Dropzone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
            file
              ? "border-emerald-400 bg-emerald-50/50"
              : "border-slate-300 hover:border-brand-500 bg-white"
          }`}
          onClick={() => document.getElementById("file-input")?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            className="hidden"
            onChange={handleFileSelect}
          />
          {file ? (
            <div className="space-y-2">
              <FileCheck className="w-12 h-12 text-emerald-600 mx-auto" />
              <p className="font-semibold text-slate-800 text-sm">{file.name}</p>
              <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB • Ready to process</p>
              <p className="text-xs text-brand-600 underline">Click to choose a different file</p>
            </div>
          ) : (
            <div className="space-y-2">
              <UploadCloud className="w-12 h-12 text-slate-400 mx-auto" />
              <p className="font-semibold text-slate-700 text-sm">
                Click or drag & drop a PDF document here
              </p>
              <p className="text-xs text-slate-400">PDF, scanned PDF, PNG, or JPG (up to 50MB)</p>
            </div>
          )}
        </div>

        {/* Title Input */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Document Title (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. Q3 Financial & Engineering Report"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
          />
        </div>

        {/* Version Association */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5">
            <GitBranch className="w-3.5 h-3.5 text-purple-600" />
            <span>Document Revision Of (Optional)</span>
          </label>
          <select
            value={parentDocId}
            onChange={(e) => setParentDocId(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white text-slate-700"
          >
            <option value="">-- None (New Root Document) --</option>
            {existingDocs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title} ({d.original_filename})
              </option>
            ))}
          </select>
          <p className="text-xs text-slate-400">
            Link to an earlier version to enable instant side-by-side difference detection.
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Progress Display */}
        {uploading && (
          <div className="p-4 rounded-xl bg-brand-50 border border-brand-200 text-brand-800 text-xs flex items-center space-x-3">
            <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
            <span>{progressStage}</span>
          </div>
        )}

        {/* Success confirmation */}
        {successDocId && !uploading && (
          <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-3">
            <div className="flex items-center space-x-2">
              <FileCheck className="w-5 h-5 text-emerald-600" />
              <p className="font-bold text-sm">Processing Complete!</p>
            </div>
            <p className="text-xs text-emerald-700">
              The document has been parsed into layout-aware blocks, tables, and vector embeddings.
            </p>
            <div className="flex space-x-2 pt-1">
              <button
                type="button"
                onClick={() => router.push(`/viewer/${successDocId}`)}
                className="bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-emerald-500 inline-flex items-center space-x-1"
              >
                <span>Open in Viewer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => router.push(`/chat?docId=${successDocId}`)}
                className="bg-white border border-emerald-300 text-emerald-800 px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-emerald-100"
              >
                Ask Questions
              </button>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!file || uploading}
          className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold py-3 px-4 rounded-xl text-sm transition-all shadow-sm flex items-center justify-center space-x-2"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing Ingestion Pipeline...</span>
            </>
          ) : (
            <>
              <UploadCloud className="w-4 h-4" />
              <span>Process Document</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
