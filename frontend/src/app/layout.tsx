import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMind | Understand your documents",
  description: "Find evidence-backed answers, compare document versions, and extract useful information from your files.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-slate-900 antialiased">
        <div className="flex min-h-screen flex-col lg:flex-row">
          <Navbar />
          <main className="app-main mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
