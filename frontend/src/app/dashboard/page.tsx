"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileText,
  GitCompareArrows,
  MessageSquareText,
  UploadCloud,
  AlertCircle,
  Database,
} from "lucide-react";
import { fetchDocuments, fetchHealth } from "@/lib/api";
import { DocumentItem } from "@/types";

type HealthStatus = { status?: string };

const actions = [
  {
    href: "/chat",
    label: "Ask with evidence",
    description: "Get grounded answers with clickable page citations.",
    icon: MessageSquareText,
    tone: "bg-rose-50 text-brand-700",
  },
  {
    href: "/compare",
    label: "Compare versions",
    description: "See what changed between two document revisions.",
    icon: GitCompareArrows,
    tone: "bg-amber-50 text-amber-700",
  },
  {
    href: "/extract",
    label: "Extract information",
    description: "Build a profile or define the fields you need.",
    icon: Database,
    tone: "bg-emerald-50 text-emerald-700",
  },
];

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const [documentsResult, healthResult] = await Promise.allSettled([
        fetchDocuments(),
        fetchHealth(),
      ]);
      if (documentsResult.status === "fulfilled") {
        setDocuments(documentsResult.value);
      } else {
        setLoadError("Could not reach the document library. Check that the API is running and try again.");
      }
      if (healthResult.status === "fulfilled") {
        setHealth(healthResult.value);
      }
      setLoading(false);
    }
    void loadData();
  }, []);

  const completedCount = documents.filter((doc) => doc.processing_status === "completed").length;
  const processingCount = documents.filter(
    (doc) => doc.processing_status === "processing" || doc.processing_status === "pending"
  ).length;
  const failedCount = documents.filter((doc) => doc.processing_status === "failed").length;
  const recentDocuments = documents.slice(0, 5);

  return (
    <div className="space-y-8">
      <section className="relative isolate flex flex-col gap-4 overflow-hidden rounded-2xl border border-white bg-gradient-to-r from-white via-white to-rose-50/80 p-5 shadow-lg shadow-slate-900/[0.04] sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <span className="pointer-events-none absolute -right-10 -top-16 -z-10 h-48 w-48 rounded-full bg-brand-100/60 blur-3xl" />
        <div className="flex items-center gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-900 text-white shadow-lg shadow-brand-900/20 ring-4 ring-brand-50">
            <FileText className="h-6 w-6" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-700">Workspace dashboard</p>
            <h1 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Welcome back to DocuMind</h1>
            <p className="mt-1 text-sm text-slate-500">Your documents, processing activity, and tools in one place.</p>
          </div>
        </div>
        <Link
          href="/upload"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#890149] px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand-900/15 transition hover:-translate-y-0.5 hover:bg-brand-800 hover:shadow-lg"
        >
          <UploadCloud className="h-4 w-4" />
          Add a document
        </Link>
      </section>

      {loadError && (
        <div role="alert" className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{loadError}</p>
        </div>
      )}

      <section aria-label="Library status" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="group relative flex items-center justify-between overflow-hidden rounded-2xl border border-white bg-white p-5 shadow-md shadow-slate-900/[0.04] transition duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <span className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-500 to-brand-200" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">In your library</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{loading ? "—" : documents.length}</p>
            <p className="mt-1 text-xs text-slate-500">Total documents</p>
          </div>
          <span className="rounded-xl bg-brand-50 p-3 text-brand-700"><FileText className="h-5 w-5" /></span>
        </div>
        <div className="group relative flex items-center justify-between overflow-hidden rounded-2xl border border-white bg-white p-5 shadow-md shadow-slate-900/[0.04] transition duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <span className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500 to-emerald-200" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Ready to explore</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-emerald-700">{loading ? "—" : completedCount}</p>
            <p className="mt-1 text-xs text-slate-500">Fully processed</p>
          </div>
          <span className="rounded-xl bg-emerald-50 p-3 text-emerald-700"><CheckCircle2 className="h-5 w-5" /></span>
        </div>
        <div className="group relative flex items-center justify-between overflow-hidden rounded-2xl border border-white bg-white p-5 shadow-md shadow-slate-900/[0.04] transition duration-200 hover:-translate-y-0.5 hover:shadow-lg">
          <span className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-amber-500 to-amber-200" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Needs attention</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-amber-700">{loading ? "—" : processingCount + failedCount}</p>
            <p className="mt-1 text-xs text-slate-500">{failedCount} failed · {processingCount} processing</p>
          </div>
          <span className="rounded-xl bg-amber-50 p-3 text-amber-700"><Clock3 className="h-5 w-5" /></span>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-700">A clearer way to work</p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">What would you like to do?</h2>
          </div>
          <Link href="/documents" className="hidden items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-900 sm:inline-flex">
            Browse library <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.href}
                href={action.href}
                className="group rounded-2xl border border-white bg-white p-5 shadow-md shadow-slate-900/[0.04] transition duration-200 hover:-translate-y-1 hover:border-brand-200 hover:shadow-xl"
              >
                <div className={`inline-flex rounded-xl p-3 ${action.tone}`}><Icon className="h-5 w-5" /></div>
                <h3 className="mt-4 font-semibold text-slate-900">{action.label}</h3>
                <p className="mt-2 min-h-10 text-sm leading-6 text-slate-600">{action.description}</p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-700">
                  Get started <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-white bg-white shadow-md shadow-slate-900/[0.04]">
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-white to-[#f3f3e7]/70 px-5 py-4">
          <div>
            <h2 className="font-semibold text-slate-900">Recently added</h2>
            <p className="mt-0.5 text-xs text-slate-500">Your latest files and their processing status</p>
          </div>
          <Link href="/documents" className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-900">
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        {recentDocuments.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700"><FileText className="h-6 w-6" /></span>
            <h3 className="mt-4 font-semibold text-slate-900">Your library starts here</h3>
            <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">Add a document to search, compare versions, and extract the information you need.</p>
            <Link href="/upload" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-brand-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-800">
              <UploadCloud className="h-4 w-4" /> Add your first document
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentDocuments.map((doc) => (
              <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition hover:bg-slate-50">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="rounded-xl bg-slate-100 p-2.5 text-slate-600"><FileText className="h-4 w-4" /></span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">{doc.title}</p>
                    <p className="mt-0.5 truncate text-xs text-slate-500">{doc.original_filename} · {doc.page_count} pages</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                    doc.processing_status === "completed" ? "bg-emerald-50 text-emerald-700" :
                    doc.processing_status === "failed" ? "bg-rose-50 text-rose-700" :
                    "bg-amber-50 text-amber-700"
                  }`}>{doc.processing_status}</span>
                  {doc.processing_status === "completed" && (
                    <Link href={`/viewer/${doc.id}`} className="text-xs font-semibold text-brand-700 hover:text-brand-900">Open</Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
