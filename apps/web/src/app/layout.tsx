import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Lithium - Discord Bot Control Center",
    template: "%s | Lithium",
  },
  description: "MEE6 benzeri premium Discord bot yönetim paneli. Sunucunuzu profesyonelce yönetin.",
  keywords: ["discord", "bot", "yönetim", "panel", "moderasyon", "lithium"],
  authors: [{ name: "Lithium Team" }],
  openGraph: {
    title: "Lithium - Discord Bot Control Center",
    description: "MEE6 benzeri premium Discord bot yönetim paneli",
    type: "website",
    locale: "tr_TR",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background`}
      >
        {children}
      </body>
    </html>
  );
}
