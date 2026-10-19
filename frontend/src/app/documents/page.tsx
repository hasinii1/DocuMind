"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  Filter,
  Trash2,
  Eye,
  MessageSquare,
  GitCompare,
  Database,
  UploadCloud,
  CheckCircle2,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { fetchDocuments, deleteDocument } from "@/lib/api";
import { DocumentItem } from "@/types";

export default function DocumentLibraryPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      setLoading(true);
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Are you sure you want to delete this document and all its chunks/citations?")) {
      return;
    }
    try {
      setDeletingId(id);
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      alert("Failed to delete document");
    } finally {
      setDeletingId(null);
    }
  }

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || doc.processing_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Document Library</h1>
          <p className="text-sm text-slate-500 mt-1">
            Organize, search, and manage your private workspace documents and their extracted artifacts.
          </p>
        </div>
        <Link
          href="/upload"
          className="inline-flex items-center space-x-2 bg-brand-600 hover:bg-brand-500 text-white font-medium px-4 py-2 rounded-xl text-sm transition-all shadow-sm"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Document</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by title or filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-200 rounded-lg text-sm px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Document Grid / Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Loading document library...</div>
      ) : filteredDocs.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
          <FileText className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="font-semibold text-slate-700">No documents found matching filters</p>
          <p className="text-xs text-slate-500">Try modifying your search or upload a new file.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocs.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
                    <FileText className="w-5 h-5" />
                  </div>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      doc.processing_status === "completed"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : doc.processing_status === "processing"
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-rose-50 text-rose-700 border border-rose-200"
                    }`}
                  >
                    {doc.processing_status}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 line-clamp-1" title={doc.title}>
                    {doc.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{doc.original_filename}</p>
                </div>

                <div className="text-xs text-slate-500 space-y-1 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <div className="flex justify-between">
                    <span>Pages:</span>
                    <span className="font-semibold text-slate-700">{doc.page_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>File size:</span>
                    <span className="font-semibold text-slate-700">{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Artifacts:</span>
                    <span className="font-semibold text-slate-700">
                      {doc.has_tables ? "Tables " : ""}
                      {doc.has_scanned_pages ? "OCR" : ""}
                      {!doc.has_tables && !doc.has_scanned_pages ? "Text" : ""}
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <Link
                    href={`/viewer/${doc.id}`}
                    className="p-1.5 text-slate-600 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
                    title="Open Document Viewer"
                  >
                    <Eye className="w-4 h-4" />
                  </Link>
                  <Link
                    href={`/chat?docId=${doc.id}`}
                    className="p-1.5 text-slate-600 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
                    title="Ask DocuMind with Evidence"
                  >
                    <MessageSquare className="w-4 h-4" />
                  </Link>
                  <Link
                    href={`/extract?docId=${doc.id}`}
                    className="p-1.5 text-slate-600 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                    title="Extract Structured Schema"
                  >
                    <Database className="w-4 h-4" />
                  </Link>
                </div>

                <button
                  onClick={() => handleDelete(doc.id)}
                  disabled={deletingId === doc.id}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
