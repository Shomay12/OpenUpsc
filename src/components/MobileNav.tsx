'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Map, 
  Clock, 
  TrendingUp, 
  User as UserIcon,
  BookOpen
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function MobileNav() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();

  return (
    <nav 
      aria-label="Mobile Navigation"
      className="lg:hidden fixed bottom-3 left-3 right-3 z-40 bg-white/90 backdrop-blur-xl border border-slate-200/80 shadow-floating rounded-full px-2 py-1 flex items-center justify-between max-w-md mx-auto select-none"
    >
      <Link
        href={isAuthenticated ? "/dashboard" : "/"}
        className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
          (pathname === '/' || pathname === '/dashboard') ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
        }`}
      >
        <LayoutDashboard className="w-4 h-4" />
        <span className="truncate">Home</span>
      </Link>

      <Link
        href="/roadmaps"
        className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
          pathname.startsWith('/roadmaps') ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
        }`}
      >
        <Map className="w-4 h-4" />
        <span className="truncate">Roadmap</span>
      </Link>

      <Link
        href={isAuthenticated ? "/study" : "/ncert"}
        className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
          (pathname.startsWith('/study') || pathname.startsWith('/ncert')) ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
        }`}
      >
        <Clock className="w-4 h-4" />
        <span className="truncate">{isAuthenticated ? "Study" : "NCERT"}</span>
      </Link>

      <Link
        href={isAuthenticated ? "/progress" : "/resources"}
        className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
          (pathname === '/progress' || pathname.startsWith('/resources')) ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
        }`}
      >
        <TrendingUp className="w-4 h-4" />
        <span className="truncate">{isAuthenticated ? "Progress" : "Resources"}</span>
      </Link>

      <Link
        href={isAuthenticated ? "/profile" : "/auth"}
        className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
          (pathname === '/profile' || pathname.startsWith('/auth')) ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
        }`}
      >
        <UserIcon className="w-4 h-4" />
        <span className="truncate">{isAuthenticated ? 'Profile' : 'Log In'}</span>
      </Link>
    </nav>
  );
}
