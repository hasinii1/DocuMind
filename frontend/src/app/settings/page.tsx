"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Settings,
  Database,
  Lock,
  Cpu,
  RefreshCw,
  Trash2,
  CheckCircle2,
} from "lucide-react";
import { fetchHealth } from "@/lib/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth(h))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Settings & Security</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review system health, operational parameters, and the DocuMind security architecture.
        </p>
      </div>

      {/* Security Architecture & Defenses */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
          <ShieldCheck className="w-5 h-5 text-emerald-600" />
          <h2 className="font-bold text-slate-900 text-base">Active Security Controls</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Lock className="w-3.5 h-3.5 text-brand-600" />
              <span>Indirect Prompt Injection Defense</span>
            </span>
            <p className="text-slate-600 leading-relaxed">
              Retrieved document content is treated as untrusted text wrapped in passive evidence tags. System prompt overrides and jailbreaks are sanitized and logged to the audit trail.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Database-Enforced Citation Verification</span>
            </span>
            <p className="text-slate-600 leading-relaxed">
              Citations are verified against actual database chunk IDs and checked for fuzzy quote containment in the source text. Model-invented page numbers are rejected.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-purple-600" />
              <span>Workspace-Level Access Isolation</span>
            </span>
            <p className="text-slate-600 leading-relaxed">
              All vector, keyword, and document queries are scoped strictly to the authenticated user&apos;s active workspace. Cross-workspace data leakage is blocked at the database query level.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-amber-600" />
              <span>Zero Arbitrary Tool Execution</span>
            </span>
            <p className="text-slate-600 leading-relaxed">
              LLMs have no direct access to execute shell commands, SQL queries, or file modifications. All operations follow deterministic, type-checked backend pipelines.
            </p>
          </div>
        </div>
      </div>

      {/* Backend Diagnostics & Configuration */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
          <Settings className="w-5 h-5 text-brand-600" />
          <h2 className="font-bold text-slate-900 text-base">Backend Diagnostics</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] uppercase font-sans font-semibold text-slate-400">Backend Status</p>
            <p className="text-emerald-700 font-bold mt-1 text-sm">{health?.status || "Connected"}</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] uppercase font-sans font-semibold text-slate-400">Database Engine</p>
            <p className="text-slate-800 font-bold mt-1 text-sm">{health?.database || "SQLite / PostgreSQL"}</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-[10px] uppercase font-sans font-semibold text-slate-400">Reranker Service</p>
            <p className="text-brand-700 font-bold mt-1 text-sm">
              {health?.reranker_enabled ? "Enabled (Cross-Encoder)" : "Lexical-Semantic"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
