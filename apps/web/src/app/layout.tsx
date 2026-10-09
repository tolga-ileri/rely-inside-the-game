import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rely Match Brain",
  description: "From football events to understanding. From understanding to decisions. Synthetic football-realistic data.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  );
}
