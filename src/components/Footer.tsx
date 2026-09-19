'use client';

import React from 'react';
import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-slate-200/80 bg-white/60 backdrop-blur-sm mt-auto">
      <div className="w-full max-w-[1500px] mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 space-y-8">
        {/* Top Minimal Editorial Row */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-1 max-w-md">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-md bg-slate-900 text-white flex items-center justify-center text-[10px] font-bold">
                O
              </div>
              <span className="font-display font-bold text-sm tracking-tight text-slate-900">
                OpenUPSC
              </span>
            </div>
            <p className="text-xs text-slate-500 font-sans leading-relaxed">
              An organized, open resource platform for UPSC preparation. Zero hype, zero ads, zero paywalls.
            </p>
          </div>

          {/* Minimal Quick Links */}
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500 font-medium">
            <Link href="/resources" className="hover:text-slate-900 transition-colors">Resources</Link>
            <Link href="/roadmaps" className="hover:text-slate-900 transition-colors">Roadmap</Link>
            <Link href="/ncert" className="hover:text-slate-900 transition-colors">NCERTs</Link>
            <Link href="/pyqs" className="hover:text-slate-900 transition-colors">PYQ Vault</Link>
            <Link href="/journey" className="hover:text-slate-900 transition-colors">About</Link>
          </div>
        </div>

        {/* Bottom Bar: Left Copyright | Middle @ProjectByShomayyy | Right Tagline */}
        <div className="grid grid-cols-1 md:grid-cols-3 items-center justify-between text-xs text-slate-400 gap-4">
          <p className="text-left text-[11px]">
            © {new Date().getFullYear()} OpenUPSC. Open academic infrastructure.
          </p>
          
          <div className="text-center">
            <span className="font-serif italic text-sm sm:text-base tracking-wide text-slate-700 hover:text-slate-900 font-medium select-none">
              @ProjectByShomayyy
            </span>
          </div>

          <p className="text-left md:text-right text-slate-400 text-[11px]">
            Designed for calm, long-term focus.
          </p>
        </div>
      </div>
    </footer>
  );
}
