import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DR Screening — AI-Assisted Retinal Image Analysis",
  description:
    "Clinical decision support system for diabetic retinopathy screening, image quality assessment, and explainable AI triage.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-100/50">
      <body className="min-h-full flex flex-col font-sans text-slate-900 antialiased selection:bg-slate-800 selection:text-white">
        {children}
      </body>
    </html>
  );
}
