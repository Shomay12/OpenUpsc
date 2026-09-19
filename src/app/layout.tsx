import type { Metadata, Viewport } from 'next';
import './globals.css';
import AppShell from '../components/AppShell';
import { AuthProvider } from '../context/AuthContext';

export const viewport: Viewport = {
  themeColor: '#0F172A',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  viewportFit: 'cover',
};

export const metadata: Metadata = {
  title: 'OpenUPSC — Structured Path to UPSC Preparation',
  description: 'An organized, open resource platform from NCERT foundations to advanced UPSC preparation, progress tracking, and structured study routines.',
  keywords: 'OpenUPSC, UPSC, NCERT, Civil Services, Free UPSC Roadmap, Prelims, Mains, IAS Preparation, Hinglish Study Guide, PYQs, UPSC App',
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/icons/icon.svg', type: 'image/svg+xml' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'OpenUPSC',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="min-h-screen bg-[#FAFAF8] text-slate-900 antialiased selection:bg-slate-900 selection:text-white relative">
        {/* Soft subtle ambient radial light in background */}
        <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[1200px] h-[600px] bg-gradient-to-b from-slate-200/30 via-slate-100/10 to-transparent blur-3xl opacity-70 rounded-full" />
        </div>
        <AuthProvider>
          <AppShell>
            {children}
          </AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
