import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { AuthProvider } from "@/contexts/auth-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Oxla Suite - All-in-One Workspace Platform",
  description: "Comprehensive workspace platform competing with Google Workspace and Microsoft 365. Email, file storage, and more.",
  keywords: ["Oxla", "workspace", "email", "file storage", "collaboration", "Next.js", "TypeScript"],
  authors: [{ name: "Oxla Team" }],
  openGraph: {
    title: "Oxla Suite",
    description: "All-in-one workspace platform for modern teams",
    url: "https://oxla.com",
    siteName: "Oxla",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Oxla Suite",
    description: "All-in-one workspace platform",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        <AuthProvider>
          {children}
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  );
}
