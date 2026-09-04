import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import BloombergTicker from "@/components/BloombergTicker";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ['400', '500', '600', '700', '800'],
});

export const metadata: Metadata = {
  title: "QuantAlpha Bloomberg Terminal — Institutional Alpha Research",
  description: "Bloomberg-style institutional alpha research platform: Data Infrastructure, Feature Engineering, Alpha Discovery, Statistical Validation, Portfolio Optimization, Risk Management, Production Monitoring.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={jetbrainsMono.variable}>
      <body className={jetbrainsMono.className} suppressHydrationWarning>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            {children}
            <BloombergTicker />
          </main>
        </div>
      </body>
    </html>
  );
}
