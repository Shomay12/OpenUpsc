'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Search,
  User as UserIcon,
  Menu,
  X,
  Sparkles,
  Calendar,
  History,
  Bookmark,
  Settings,
  LogOut,
  LayoutDashboard,
  ChevronRight,
  Flame,
  Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { InstallAppButton } from './InstallAppPrompt';

interface HeaderProps {
  onOpenSearch: () => void;
}

export default function Header({ onOpenSearch }: HeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, profile, isAuthenticated, signOut } = useAuth();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setProfileDropdownOpen(false);
  }, [pathname]);

  const handleLogout = async () => {
    await signOut();
    router.push('/auth');
  };

  const displayName = profile?.name || user?.email?.split('@')[0] || 'Aspirant';
  const initial = displayName.charAt(0).toUpperCase();

  // Get Breadcrumb label from pathname
  const getBreadcrumb = () => {
    if (pathname === '/' || pathname === '/dashboard') return 'Workspace Dashboard';
    if (pathname.startsWith('/ncert')) return 'NCERT Academic Foundation';
    if (pathname.startsWith('/roadmaps')) return 'Syllabus Roadmaps';
    if (pathname.startsWith('/resources')) return 'Resource Library';
    if (pathname === '/study') return 'Distraction-Free Timer';
    if (pathname === '/study/today') return 'Today’s Study Plan';
    if (pathname === '/study/timetable') return 'Timetable Schedule';
    if (pathname === '/study/history') return 'Study History & Analytics';
    if (pathname.startsWith('/pyqs')) return 'PYQ Vault';
    if (pathname.startsWith('/current-affairs')) return 'Current Affairs Integration';
    if (pathname.startsWith('/progress')) return 'Syllabus Progress';
    if (pathname.startsWith('/saved')) return 'Saved Bookmarks';
    if (pathname.startsWith('/profile')) return 'Profile & Stage';
    if (pathname.startsWith('/settings')) return 'Preferences & Settings';
    if (pathname.startsWith('/journey')) return 'Preparation Philosophy';
    return 'OpenUPSC';
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 flex items-center justify-between select-none">
      {/* Left side: Mobile Brand OR Desktop Breadcrumbs */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Mobile Logo (< 1024px) */}
        <div className="flex lg:hidden items-center gap-2 flex-shrink-0">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center font-display font-extrabold text-xs shadow-sm">
              O
            </div>
            <span className="font-display font-bold text-sm tracking-tight text-slate-900">
              OpenUPSC
            </span>
          </Link>
        </div>

        {/* Desktop Breadcrumbs (>= 1024px) */}
        <div className="hidden lg:flex items-center gap-2 text-xs text-slate-500 font-medium">
          <span className="text-slate-400">OpenUPSC</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <span className="text-slate-900 font-semibold">{getBreadcrumb()}</span>
        </div>
      </div>

      {/* Right side: Search, Status, Profile, Mobile Menu */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Search Command Trigger */}
        <button
          type="button"
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100/90 hover:bg-slate-200/80 text-slate-600 text-xs font-medium transition-colors"
        >
          <Search className="w-3.5 h-3.5 text-slate-500" />
          <span className="hidden sm:inline text-[11px] text-slate-500">Quick Search</span>
          <kbd className="hidden md:inline-flex items-center text-[10px] text-slate-400 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
            ⌘K
          </kbd>
        </button>

        {/* Target Horizon Badge (Desktop) */}
        <div className="hidden xl:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-50 border border-slate-200/80 text-[11px] font-mono text-slate-600">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>CSE {profile?.targetAttemptYear || '2028'} Horizon</span>
        </div>

        {/* Install Chrome App Button */}
        <div className="hidden sm:block">
          <InstallAppButton />
        </div>

        {/* Profile Dropdown or Auth Trigger */}
        {isAuthenticated ? (
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-display font-bold text-xs shadow-sm hover:ring-2 hover:ring-slate-300 transition-all"
              title={displayName}
            >
              {initial}
            </button>

            {profileDropdownOpen && (
              <div className="absolute top-full right-0 mt-2 w-60 bg-white/95 backdrop-blur-2xl border border-slate-200/90 rounded-2xl p-2 shadow-command space-y-1 animate-in zoom-in-95 duration-100 text-xs font-sans z-50">
                <div className="px-3 py-2 border-b border-slate-100">
                  <p className="font-semibold text-slate-900 line-clamp-1">{displayName}</p>
                  <p className="text-[11px] text-slate-400 font-mono line-clamp-1">{user?.email || profile?.email || ''}</p>
                </div>

                <Link
                  href="/dashboard"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-700"
                >
                  <LayoutDashboard className="w-3.5 h-3.5 text-slate-500" />
                  <span>Workspace Dashboard</span>
                </Link>

                <Link
                  href="/profile"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-700"
                >
                  <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                  <span>Profile & Stage</span>
                </Link>

                <Link
                  href="/study/today"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-700"
                >
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  <span>Today’s Plan & Timetable</span>
                </Link>

                <Link
                  href="/study/history"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-700"
                >
                  <History className="w-3.5 h-3.5 text-slate-500" />
                  <span>Study History & Logs</span>
                </Link>

                <Link
                  href="/saved"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-700"
                >
                  <Bookmark className="w-3.5 h-3.5 text-slate-500" />
                  <span>Saved Resources</span>
                </Link>

                <Link
                  href="/settings"
                  onClick={() => setProfileDropdownOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-50 text-slate-700"
                >
                  <Settings className="w-3.5 h-3.5 text-slate-500" />
                  <span>Settings</span>
                </Link>

                <div className="pt-1 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-rose-50 text-rose-600 transition-colors text-left"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Log Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            <Link
              href="/auth"
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              Log in
            </Link>
            <Link
              href="/auth?mode=signup"
              className="px-4 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
            >
              Sign up
            </Link>
          </div>
        )}

        {/* Mobile Hamburger Drawer (< 1024px) */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-1.5 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer Overlay (< 1024px) */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-x-0 top-16 bg-white/95 backdrop-blur-2xl border-b border-slate-200/90 shadow-command p-4 space-y-3 animate-in slide-in-from-top-2 duration-150 z-50">
          <div className="grid grid-cols-2 gap-2 text-xs font-medium">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center font-semibold"
            >
              Home / Dashboard
            </Link>
            <Link
              href="/roadmaps"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center"
            >
              Roadmaps
            </Link>
            <Link
              href="/resources"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center"
            >
              Resources
            </Link>
            <Link
              href="/ncert"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center"
            >
              NCERT Curriculum
            </Link>
            <Link
              href="/study"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-900 text-white text-center font-semibold"
            >
              Focus Timer
            </Link>
            <Link
              href="/study/today"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center"
            >
              Today’s Plan
            </Link>
            <Link
              href="/pyqs"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center"
            >
              PYQ Vault
            </Link>
            <Link
              href="/current-affairs"
              onClick={() => setMobileMenuOpen(false)}
              className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 text-center"
            >
              Current Affairs
            </Link>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
            <Link
              href="/profile"
              onClick={() => setMobileMenuOpen(false)}
              className="p-2 text-slate-600 hover:text-slate-900 font-medium"
            >
              Profile & Stage
            </Link>
            <Link
              href="/settings"
              onClick={() => setMobileMenuOpen(false)}
              className="p-2 text-slate-600 hover:text-slate-900 font-medium"
            >
              Settings
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
