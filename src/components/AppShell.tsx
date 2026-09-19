'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import MobileNav from './MobileNav';
import Footer from './Footer';
import SearchCommand from './SearchCommand';
import InstallAppPrompt from './InstallAppPrompt';

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const [searchOpen, setSearchOpen] = useState(false);

  // Global ⌘K shortcut listener
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-[#FAFAF8] text-slate-900 antialiased selection:bg-slate-900 selection:text-white">
      {/* Persistent Left Desktop Sidebar (>= 1024px) */}
      <Sidebar onOpenSearch={() => setSearchOpen(true)} />

      {/* Main Application Area (Pushed right by sidebar on >= 1024px) */}
      <div className="lg:pl-60 xl:pl-64 flex flex-col flex-1 min-h-screen w-full">
        {/* Top Application Header */}
        <Header onOpenSearch={() => setSearchOpen(true)} />

        {/* Dynamic Main Workspace Canvas */}
        <main className="flex-1 w-full max-w-[1500px] mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8 pb-24 lg:pb-12">
          {children}
        </main>

        {/* Desktop & Mobile App Footer */}
        <Footer />
      </div>

      {/* Floating Bottom Navigation (< 1024px) */}
      <MobileNav />

      {/* ⌘K Command Search Modal */}
      <SearchCommand isOpen={searchOpen} onClose={() => setSearchOpen(false)} />

      {/* Chrome App / PWA Install Prompt */}
      <InstallAppPrompt />
    </div>
  );
}
