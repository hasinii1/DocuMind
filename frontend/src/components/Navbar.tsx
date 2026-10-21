"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  FileText,
  LayoutDashboard,
  UploadCloud,
  MessageSquareText,
  GitCompare,
  Database,
  Settings,
  ShieldCheck,
  LogOut,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Library", icon: FileText },
  { href: "/upload", label: "Upload", icon: UploadCloud },
  { href: "/chat", label: "Ask DocuMind", icon: MessageSquareText },
  { href: "/compare", label: "Compare Versions", icon: GitCompare },
  { href: "/extract", label: "Structured Extraction", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  function exitApplication() {
    router.push("/");
  }

  if (pathname === "/") return null;

  return (
    <aside className="sticky top-0 z-50 w-full shrink-0 border-b border-slate-200/80 bg-white/95 shadow-[0_8px_30px_rgba(15,23,42,0.03)] backdrop-blur-xl lg:h-screen lg:w-64 lg:border-b-0 lg:border-r lg:border-r-brand-100/70 lg:shadow-[8px_0_30px_rgba(15,23,42,0.03)]">
      <div className="flex flex-col lg:h-full">
        <div className="flex h-16 items-center justify-between px-4 lg:h-auto lg:px-5 lg:py-6">
          <Link href="/" className="group flex items-center space-x-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 via-brand-600 to-brand-400 text-white shadow-md shadow-brand-500/20 transition-transform group-hover:scale-105">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900">DocuMind</span>
              <span className="ml-1.5 rounded border border-brand-200 bg-brand-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-700">
                AI RAG
              </span>
            </div>
          </Link>
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 bg-slate-200 text-xs font-semibold text-slate-700 lg:hidden">
            DM
          </div>
        </div>

        <nav
          aria-label="Main navigation"
          className="flex items-center gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:items-stretch lg:overflow-visible lg:px-3 lg:py-3"
        >
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = item.href === "/" ? pathname === "/" : pathname === item.href || pathname?.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`relative flex shrink-0 items-center space-x-2 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 lg:w-full ${
                  isActive
                    ? "bg-gradient-to-r from-brand-50 to-white font-semibold text-brand-800 shadow-sm ring-1 ring-inset ring-brand-100"
                    : "text-slate-600 hover:translate-x-0.5 hover:bg-slate-50 hover:text-brand-800"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-brand-600" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-100 bg-gradient-to-b from-white to-[#f3f3e7]/55 px-3 py-3 lg:px-4 lg:py-4">
          <div className="mb-3 hidden items-center space-x-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs text-emerald-700 lg:flex">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Grounded Verification</span>
          </div>
          <button
            type="button"
            onClick={exitApplication}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 transition-colors hover:bg-rose-50 hover:text-brand-700"
            title="Return to the DocuMind welcome page"
          >
            <LogOut className="h-4 w-4" />
            <span>Exit</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
