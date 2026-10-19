"use client";

import React from "react";
import Link from "next/link";
import { RetrievedEvidence } from "@/types";
import { X, Layers, ExternalLink, ShieldCheck } from "lucide-react";

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: RetrievedEvidence[];
}

export default function EvidenceDrawer({ isOpen, onClose, evidence }: EvidenceDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-white shadow-2xl border-l border-slate-200 z-50 flex flex-col">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-brand-600" />
          <h2 className="text-sm font-bold text-slate-900">
            Retrieved Evidence Chunks ({evidence.length})
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {evidence.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-8">
            No evidence chunks associated with this response.
          </p>
        ) : (
          evidence.map((chunk, idx) => (
            <div
              key={chunk.chunk_id || idx}
              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">
                  {chunk.section_title || `Section`} • Page {chunk.page_start}
                </span>
                <span className="text-[10px] bg-brand-50 text-brand-700 px-1.5 py-0.5 rounded font-mono">
                  Score: {chunk.score.toFixed(3)}
                </span>
              </div>

              <p className="text-slate-700 leading-relaxed font-sans bg-white p-2.5 rounded-lg border border-slate-200">
                {chunk.content}
              </p>

              <div className="pt-1 flex justify-end">
                <Link
                  href={`/viewer/${chunk.document_id}?page=${chunk.page_start}`}
                  className="text-brand-600 font-semibold hover:underline inline-flex items-center space-x-1 text-[11px]"
                >
                  <span>Verify on Page {chunk.page_start}</span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
