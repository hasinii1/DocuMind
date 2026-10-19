"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Citation } from "@/types";
import { ShieldCheck, AlertCircle, ExternalLink } from "lucide-react";

interface CitationBadgeProps {
  citation: Citation;
}

export default function CitationBadge({ citation }: CitationBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative inline-block my-1 mr-1.5">
      <button
        onClick={() => setShowTooltip(!showTooltip)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="inline-flex items-center space-x-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200 px-2 py-0.5 rounded-md text-xs font-semibold transition-colors"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-brand-600"></span>
        <span>
          {citation.document_title ? `${citation.document_title.slice(0, 16)}... ` : ""}
          P.{citation.page_number}
        </span>
      </button>

      {/* Tooltip Card */}
      {showTooltip && (
        <div className="absolute bottom-full left-0 mb-2 w-80 bg-white border border-slate-200 shadow-xl rounded-xl p-3 z-50 text-xs space-y-2 pointer-events-auto">
          <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
            <span className="font-bold text-slate-800">
              Verified Source: Page {citation.page_number}
            </span>
            <span className="inline-flex items-center space-x-1 text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span>Grounded</span>
            </span>
          </div>

          <p className="text-slate-600 italic bg-slate-50 p-2 rounded-lg border border-slate-100 font-serif leading-relaxed">
            &ldquo;{citation.quote}&rdquo;
          </p>

          <div className="flex justify-between items-center text-[10px] text-slate-400 pt-1">
            <span>Confidence: {Math.round(citation.confidence_score * 100)}%</span>
            <Link
              href={`/viewer/${citation.document_id}?page=${citation.page_number}`}
              className="text-brand-600 font-semibold hover:underline inline-flex items-center space-x-1"
            >
              <span>Open Document Page</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
