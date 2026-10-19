"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  Download,
  MessageSquare,
  Layers,
  ExternalLink,
} from "lucide-react";
import { fetchDocument, fetchPageElements, getDocumentDownloadUrl } from "@/lib/api";
import { DocumentItem, DocumentElement } from "@/types";

function ViewerContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const docId = params.id as string;
  const initialPage = parseInt(searchParams.get("page") || "1", 10);

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(initialPage);
  const [elements, setElements] = useState<DocumentElement[]>([]);
  const [loading, setLoading] = useState(true);
  const [elementsLoading, setElementsLoading] = useState(false);

  useEffect(() => {
    async function loadDoc() {
      try {
        setLoading(true);
        const d = await fetchDocument(docId);
        setDocument(d);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadDoc();
  }, [docId]);

  useEffect(() => {
    async function loadElements() {
      if (!docId) return;
      try {
        setElementsLoading(true);
        const data = await fetchPageElements(docId, currentPage);
        setElements(data.elements || []);
      } catch (err) {
        console.error(err);
      } finally {
        setElementsLoading(false);
      }
    }
    loadElements();
  }, [docId, currentPage]);

  const totalPages = document?.page_count || 1;
  const downloadUrl = getDocumentDownloadUrl(docId);

  return (
    <div className="space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-3">
          <Link
            href="/documents"
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100"
            title="Back to library"
          >
            <ChevronLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-base font-bold text-slate-900 line-clamp-1">{document?.title || "Document Viewer"}</h1>
            <p className="text-xs text-slate-400">
              {document?.original_filename} • {totalPages} pages total
            </p>
          </div>
        </div>

        {/* Page navigation controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 rounded-lg p-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="p-1 rounded text-slate-600 hover:bg-white disabled:opacity-30"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-semibold px-2 text-slate-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="p-1 rounded text-slate-600 hover:bg-white disabled:opacity-30"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <a
            href={downloadUrl}
            target="_blank"
            rel="noreferrer"
            className="p-2 border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg text-xs font-semibold inline-flex items-center space-x-1"
            title="Download PDF"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Raw PDF</span>
          </a>

          <Link
            href={`/chat?docId=${docId}`}
            className="bg-brand-600 hover:bg-brand-500 text-white px-3 py-2 rounded-lg text-xs font-semibold inline-flex items-center space-x-1.5"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Ask DocuMind</span>
          </Link>
        </div>
      </div>

      {/* Main Split Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[680px]">
        {/* Left: Original Document Preview (embed / iframe) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
          <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-600">
            <span className="flex items-center space-x-1.5">
              <FileText className="w-4 h-4 text-brand-600" />
              <span>Original Document View (Page {currentPage})</span>
            </span>
            <a
              href={`${downloadUrl}#page=${currentPage}`}
              target="_blank"
              rel="noreferrer"
              className="text-brand-600 hover:underline inline-flex items-center space-x-1"
            >
              <span>Full Screen</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="flex-1 bg-slate-100 flex items-center justify-center p-2">
            <iframe
              src={`${downloadUrl}#page=${currentPage}&toolbar=0&navpanes=0`}
              className="w-full h-full min-h-[600px] rounded-lg border border-slate-300 bg-white"
              title="PDF Viewer"
            />
          </div>
        </div>

        {/* Right: Extracted Elements & Layout Metadata */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-purple-600" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Extracted Page {currentPage} Elements ({elements.length})
              </h2>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[640px]">
            {elementsLoading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading extracted elements...</div>
            ) : elements.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No individual text blocks or tables registered for Page {currentPage}.
              </div>
            ) : (
              elements.map((el, i) => (
                <div
                  key={el.id || i}
                  className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-slate-50 hover:border-slate-300 transition-colors space-y-1.5 text-xs"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span
                      className={`font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${
                        el.element_type === "heading"
                          ? "bg-purple-100 text-purple-800"
                          : el.element_type === "table"
                          ? "bg-blue-100 text-blue-800"
                          : el.element_type === "ocr_text"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-200 text-slate-700"
                      }`}
                    >
                      {el.element_type}
                    </span>
                    <span className="text-slate-400 font-mono text-[10px]">
                      {el.source_method}
                    </span>
                  </div>

                  {el.element_type === "table" ? (
                    <div className="overflow-x-auto font-mono text-[11px] bg-white p-2 rounded border border-slate-200">
                      <pre className="whitespace-pre-wrap">{el.content}</pre>
                    </div>
                  ) : (
                    <p className="text-slate-800 leading-relaxed whitespace-pre-wrap">
                      {el.content}
                    </p>
                  )}

                  {el.bounding_box && (
                    <div className="text-[10px] text-slate-400 font-mono">
                      bbox: ({el.bounding_box.x0}, {el.bounding_box.y0}) - ({el.bounding_box.x1}, {el.bounding_box.y1})
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DocumentViewerPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading Document Viewer...</div>}>
      <ViewerContent />
    </Suspense>
  );
}
