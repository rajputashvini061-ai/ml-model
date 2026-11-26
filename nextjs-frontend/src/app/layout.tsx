import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SISTec Course Recommendation System",
  description: "Pre-loaded Next.js frontend powered by SISTec TF-IDF & Cosine Similarity ML API.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
