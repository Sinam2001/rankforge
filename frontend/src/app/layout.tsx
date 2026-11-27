import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RankForge — Hybrid E-Commerce Search Engine",
  description: "BM25 + Trigram + pgvector HNSW + Reciprocal Rank Fusion Search Workbench",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
