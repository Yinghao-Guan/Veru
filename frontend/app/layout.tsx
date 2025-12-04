import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Analytics } from "@vercel/analytics/react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL('https://veru.app'),
  title: {
    default: "Veru | AI Citation Checker & Hallucination Detector",
    template: "%s | Veru"
  },
  description: "Free academic tool to verify ChatGPT/Claude citations against real databases (OpenAlex). Detect fake references and AI hallucinations instantly.",
  keywords: ["AI citation checker", "verify chatgpt citations", "AI hallucination detector", "academic audit tool", "fake reference finder", "Veru app"],
  authors: [{ name: "Veru Team" }],
  creator: "Veru Team",
  publisher: "Veru",
  openGraph: {
    title: "Veru - Verify AI Citations Instantly",
    description: "Don't let AI hallucinations ruin your research. Audit citations against 250M+ real academic papers.",
    url: 'https://veru.app',
    siteName: 'Veru',
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: "Veru - AI Citation Auditor",
    description: "Detect fake AI citations instantly.",
  },
  icons: {
    icon: '/icon',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}