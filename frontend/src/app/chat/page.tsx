"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  MessageSquareText,
  Send,
  Loader2,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Layers,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import {
  createConversation,
  fetchConversations,
  fetchConversationMessages,
  askQuestion,
  fetchDocuments,
} from "@/lib/api";
import { ChatMessage, DocumentItem, RetrievedEvidence } from "@/types";
import CitationBadge from "@/components/CitationBadge";
import EvidenceDrawer from "@/components/EvidenceDrawer";

function ChatContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("docId");

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>(
    initialDocId ? [initialDocId] : []
  );
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeEvidence, setActiveEvidence] = useState<RetrievedEvidence[]>([]);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function init() {
      try {
        const [docs, convs] = await Promise.all([
          fetchDocuments().catch(() => []),
          fetchConversations().catch(() => []),
        ]);
        setDocuments(docs);

        if (convs && convs.length > 0) {
          setConversationId(convs[0].id);
          const history = await fetchConversationMessages(convs[0].id);
          setMessages(history);
        } else {
          const newConv = await createConversation("Primary Document Q&A");
          setConversationId(newConv.id);
        }
      } catch (err) {
        console.error(err);
      }
    }
    init();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSendMessage(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || !conversationId || loading) return;

    const question = inputQuery.trim();
    setInputQuery("");

    const userMsg: ChatMessage = {
      id: "temp_" + Date.now(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await askQuestion(
        conversationId,
        question,
        selectedDocIds.length > 0 ? selectedDocIds : undefined
      );

      const assistantMsg: ChatMessage = {
        id: res.message_id || "resp_" + Date.now(),
        role: "assistant",
        content: res.answer,
        citations: res.citations || [],
        retrieved_evidence: res.retrieved_evidence || [],
        insufficient_evidence: res.insufficient_evidence,
        security_warning: res.security_warning,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      if (res.retrieved_evidence && res.retrieved_evidence.length > 0) {
        setActiveEvidence(res.retrieved_evidence);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: "err_" + Date.now(),
          role: "assistant",
          content: `Error: ${err.message || "Failed to generate answer"}`,
          insufficient_evidence: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function toggleDocSelection(id: string) {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[720px]">
      {/* Left Sidebar */}
      <div className="lg:col-span-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
              <FileText className="w-4 h-4 text-brand-600" />
              <span>Target Documents</span>
            </h2>
            <span className="text-[10px] text-slate-400">
              {selectedDocIds.length === 0 ? "All Documents" : `${selectedDocIds.length} Selected`}
            </span>
          </div>

          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {documents.length === 0 ? (
              <p className="text-xs text-slate-400 py-3">No documents in library.</p>
            ) : (
              documents.map((d) => {
                const isSelected = selectedDocIds.includes(d.id);
                return (
                  <button
                    key={d.id}
                    onClick={() => toggleDocSelection(d.id)}
                    className={`w-full text-left p-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between border ${
                      isSelected
                        ? "bg-brand-50 border-brand-200 text-brand-800"
                        : "bg-white border-slate-100 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <span className="line-clamp-1 flex-1 pr-2">{d.title}</span>
                    <span
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        isSelected ? "bg-brand-600" : "bg-slate-300"
                      }`}
                    ></span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Preset Sample Prompts */}
        <div className="space-y-2 pt-4 border-t border-slate-100">
          <p className="text-[11px] font-bold uppercase text-slate-400">Sample Inquiries</p>
          <button
            onClick={() => {
              setInputQuery(
                "What were the three main causes of the reported increase in operating costs, and what evidence supports each cause?"
              );
            }}
            className="w-full text-left p-2 rounded-lg bg-slate-50 hover:bg-brand-50 hover:text-brand-700 text-[11px] text-slate-600 border border-slate-200 transition-colors"
          >
            &ldquo;What were the 3 causes of operating cost increases?&rdquo;
          </button>
          <button
            onClick={() => {
              setInputQuery(
                "What was the total Q3 revenue according to the financial summary table?"
              );
            }}
            className="w-full text-left p-2 rounded-lg bg-slate-50 hover:bg-brand-50 hover:text-brand-700 text-[11px] text-slate-600 border border-slate-200 transition-colors"
          >
            &ldquo;What was the total Q3 revenue in the table?&rdquo;
          </button>
        </div>
      </div>

      {/* Main Chat Conversation Area */}
      <div className="lg:col-span-9 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center">
              <MessageSquareText className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Ask DocuMind Engine</h2>
              <p className="text-[11px] text-slate-500">
                Grounded Hybrid Retrieval with Source-Page Citations & Strict Abstention
              </p>
            </div>
          </div>

          {activeEvidence.length > 0 && (
            <button
              onClick={() => setIsEvidenceOpen(true)}
              className="text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition-colors"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Evidence Drawer ({activeEvidence.length})</span>
            </button>
          )}
        </div>

        {/* Message History */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5 max-h-[520px]">
          {messages.length === 0 ? (
            <div className="text-center py-16 space-y-3 max-w-md mx-auto">
              <div className="w-12 h-12 bg-brand-50 text-brand-600 rounded-2xl flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-800 text-sm">Grounded Intelligence Ready</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ask questions about your uploaded PDFs. Every claim is validated against retrieved chunks and linked to the exact page.
              </p>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-sm ${
                    m.role === "user"
                      ? "bg-brand-600 text-white rounded-br-none"
                      : "bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>

                  {m.insufficient_evidence && (
                    <div className="mt-2.5 p-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center space-x-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-amber-600" />
                      <span>The documents do not contain sufficient evidence to formulate this claim.</span>
                    </div>
                  )}

                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-200">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center space-x-1">
                        <ShieldCheck className="w-3 h-3 text-emerald-600" />
                        <span>Source Citations:</span>
                      </p>
                      <div className="flex flex-wrap">
                        {m.citations.map((c, i) => (
                          <CitationBadge key={i} citation={c} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex items-center space-x-2 text-xs text-slate-400 p-3">
              <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
              <span>Searching chunks, ranking fusion, and verifying source citations...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 bg-white flex space-x-2">
          <input
            type="text"
            placeholder="Ask a question across your documents..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || loading}
            className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center space-x-1.5 shadow-sm"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Ask</span>
          </button>
        </form>
      </div>

      <EvidenceDrawer
        isOpen={isEvidenceOpen}
        onClose={() => setIsEvidenceOpen(false)}
        evidence={activeEvidence}
      />
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading DocuMind Chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}
