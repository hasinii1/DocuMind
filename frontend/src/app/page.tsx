import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Check,
  FileSearch,
  FileText,
  GitCompareArrows,
  Layers3,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";

const capabilities = [
  {
    icon: MessageSquareText,
    title: "Ask your documents",
    description: "Get answers grounded in your files, with citations that take you to the source page.",
  },
  {
    icon: GitCompareArrows,
    title: "Compare versions",
    description: "Upload two revisions and review text that was added, removed, or changed.",
  },
  {
    icon: FileSearch,
    title: "Extract what matters",
    description: "Build a document overview or define custom fields for the information you need.",
  },
];

export default function LandingPage() {
  return (
    <div className="landing-page space-y-12 pb-8 sm:space-y-16">
      <header className="landing-header sticky top-3 z-20 flex items-center justify-between rounded-2xl border px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-3" aria-label="DocuMind home">
          <span className="landing-logo flex h-10 w-10 items-center justify-center rounded-xl bg-[#890149] text-white shadow-md shadow-brand-900/20">
            <Layers3 className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-base font-bold tracking-tight text-slate-900">DocuMind</span>
            <span className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Document intelligence</span>
          </span>
        </Link>
        <nav aria-label="Landing page navigation" className="flex items-center gap-3 sm:gap-6">
          <Link href="#modules" className="hidden text-sm font-medium text-slate-600 transition hover:text-brand-700 sm:inline">
            What you can do
          </Link>
          <Link href="#built" className="hidden text-sm font-medium text-slate-600 transition hover:text-brand-700 sm:inline">
            How it works
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-[#890149] px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand-900/15 transition hover:-translate-y-0.5 hover:bg-brand-800 hover:shadow-lg"
          >
            Launch dashboard <ArrowRight className="h-4 w-4" />
          </Link>
        </nav>
      </header>

      <section className="landing-hero relative isolate overflow-hidden rounded-[2rem] px-6 py-12 text-white shadow-2xl shadow-brand-950/20 sm:px-10 sm:py-16 lg:px-14 lg:py-20">
        <div className="landing-glow pointer-events-none absolute -right-28 -top-32 -z-10 h-96 w-96 rounded-full bg-brand-300/35 blur-3xl" />
        <div className="landing-glow pointer-events-none absolute -bottom-40 right-[28%] -z-10 h-80 w-80 rounded-full bg-rose-200/15 blur-3xl" />
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-[0.08] [background-image:linear-gradient(rgba(255,255,255,0.5)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.5)_1px,transparent_1px)] [background-size:52px_52px] [mask-image:linear-gradient(110deg,black,transparent_75%)]" />
        <div className="grid items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-rose-100">
              <Sparkles className="h-3.5 w-3.5" />
              Welcome to DocuMind
            </span>
            <h1 className="mt-6 text-4xl font-semibold leading-[1.08] tracking-tight sm:text-6xl">
              Make your documents
              <span className="block text-rose-200">work for you.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-rose-100/80">
              One calm place to organize documents, find answers with evidence, compare versions,
              and extract useful information from files.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-xl bg-[#f3f3e7] px-5 py-3 text-sm font-semibold text-brand-900 shadow-lg shadow-black/15 transition hover:-translate-y-0.5 hover:bg-white hover:shadow-xl"
              >
                Launch dashboard <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-5 py-3 text-sm font-semibold text-white backdrop-blur-sm transition hover:-translate-y-0.5 hover:border-white/35 hover:bg-white/10"
              >
                <UploadCloud className="h-4 w-4" />
                Upload a document
              </Link>
            </div>
            <div className="mt-7 flex flex-wrap gap-x-5 gap-y-2 text-xs text-rose-100/70">
              <span className="inline-flex items-center gap-1.5"><Check className="h-4 w-4 text-rose-200" /> Page-linked evidence</span>
              <span className="inline-flex items-center gap-1.5"><Check className="h-4 w-4 text-rose-200" /> Flexible field extraction</span>
            </div>
          </div>

          <div className="mx-auto w-full max-w-md">
            <div className="landing-float rounded-2xl border border-white/20 bg-white/10 p-4 shadow-2xl backdrop-blur-xl sm:p-5">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-800 text-white shadow-lg shadow-black/20">
                    <FileText className="h-5 w-5" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold">Your document workspace</p>
                    <p className="mt-0.5 text-xs text-rose-100/60">A little more clarity, page by page</p>
                  </div>
                </div>
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.6)]" />
              </div>
              <div className="space-y-3 py-4">
                <div className="flex items-center gap-3 rounded-xl bg-[#f3f3e7] p-3 text-slate-800">
                  <span className="rounded-lg bg-brand-100 p-2 text-brand-700"><BookOpen className="h-4 w-4" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold">Research notes.pdf</p>
                    <p className="mt-1 text-[11px] text-slate-500">Searchable · source pages included</p>
                  </div>
                  <Check className="h-4 w-4 text-emerald-600" />
                </div>
                <div className="rounded-xl border border-white/10 bg-black/15 p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-rose-100/70">
                    <MessageSquareText className="h-4 w-4 text-rose-200" />
                    Ask a question
                  </div>
                  <p className="mt-3 rounded-lg bg-white/10 px-3 py-2.5 text-xs text-white/90">
                    “What are the main topics in this file?”
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-rose-100/70">
                    <ShieldCheck className="h-4 w-4 text-emerald-300" />
                    Answer linked to the original page
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section aria-label="How DocuMind works" className="mx-auto -mt-2 grid max-w-5xl grid-cols-1 gap-3 rounded-2xl border border-white/70 bg-white/65 p-3 shadow-sm backdrop-blur sm:grid-cols-3 sm:p-4">
        {[
          { number: "01", title: "Add your files", text: "Bring your PDFs into one workspace." },
          { number: "02", title: "Let DocuMind organize", text: "Text, sections, and page references are prepared." },
          { number: "03", title: "Find what you need", text: "Ask, compare, or extract with sources in view." },
        ].map((step) => (
          <div key={step.number} className="landing-step relative flex items-start gap-3 rounded-xl px-3 py-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-[11px] font-bold text-brand-700">{step.number}</span>
            <div>
              <p className="text-sm font-semibold text-slate-900">{step.title}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{step.text}</p>
            </div>
          </div>
        ))}
      </section>

      <section id="modules" className="mx-auto max-w-5xl scroll-mt-6">
        <div className="mx-auto mb-8 max-w-xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-700">Simple, useful tools</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            From long files to clear next steps
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Start with your documents, then choose the way you want to work with them.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {capabilities.map(({ icon: Icon, title, description }) => (
            <article key={title} className="landing-card group relative overflow-hidden rounded-2xl border border-white bg-white p-6 transition duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-xl">
              <span className="absolute right-0 top-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-brand-50 transition-transform duration-300 group-hover:scale-150" />
              <span className="relative inline-flex rounded-xl bg-brand-50 p-3 text-brand-700 transition group-hover:bg-[#890149] group-hover:text-white"><Icon className="h-5 w-5" /></span>
              <h3 className="relative mt-4 font-semibold text-slate-900">{title}</h3>
              <p className="relative mt-2 text-sm leading-6 text-slate-600">{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="built" className="relative isolate flex scroll-mt-6 flex-col items-start justify-between gap-5 overflow-hidden rounded-2xl border border-brand-100 bg-gradient-to-br from-white via-[#f3f3e7] to-rose-50 p-6 shadow-lg shadow-brand-950/5 sm:flex-row sm:items-center sm:p-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-700">Ready when you are</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Start with one document.</h2>
          <p className="mt-1 text-sm text-slate-600">Upload a file and explore it in your workspace.</p>
        </div>
        <Link href="/upload" className="inline-flex items-center gap-2 rounded-xl bg-[#890149] px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-800">
          <UploadCloud className="h-4 w-4" /> Upload a document <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </div>
  );
}
