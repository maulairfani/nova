import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nova — MCN Group Internal Assistant",
  description: "Ask Nova about company SOPs, business unit data, or anything else.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
