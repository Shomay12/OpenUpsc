'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  Search, 
  BookOpen, 
  Map, 
  CheckSquare, 
  User as UserIcon, 
  Menu, 
  X, 
  Sparkles, 
  ArrowRight, 
  Clock, 
  Calendar, 
  History, 
  Bookmark, 
  TrendingUp, 
  ChevronDown,
  Settings,
  LogOut,
  LayoutDashboard
} from 'lucide-react';
import SearchCommand from './SearchCommand';
import { InstallAppButton } from './InstallAppPrompt';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, profile, isAuthenticated, signOut, isLoading } = useAuth();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [studyDropdownOpen, setStudyDropdownOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const studyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
      if (studyRef.current && !studyRef.current.contains(e.target as Node)) {
        setStudyDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
    setProfileDropdownOpen(false);
    setStudyDropdownOpen(false);
  }, [pathname]);

  const initials = profile?.name
    ? profile.name.charAt(0).toUpperCase()
    : user?.email
    ? user.email.charAt(0).toUpperCase()
    : 'U';

  const studySublinks = [
    { href: '/study', label: 'Focus Timer', desc: 'Distraction-free 25/50m study timer' },
    { href: '/study/today', label: 'Today’s Plan', desc: 'Daily timeline and active sessions' },
    { href: '/study/timetable', label: 'Timetable Schedule', desc: 'Recurring weekly study blocks' },
    { href: '/study/history', label: 'Session History', desc: 'Weekly analytics and completed logs' },
  ];

  const handleLogout = async () => {
    await signOut();
    router.push('/auth');
  };

  const isStudyActive = pathname.startsWith('/study');

  return (
    <>
      <header className="fixed top-3 left-0 right-0 z-40 px-3 sm:px-6 pointer-events-none">
        <div className="max-w-5xl mx-auto flex items-center justify-between pointer-events-auto">
          {/* Main Floating Capsule */}
          <div className="w-full bg-white/85 backdrop-blur-xl border border-black/[0.07] shadow-sm rounded-full px-3.5 sm:px-5 py-2 flex items-center justify-between gap-3">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 flex-shrink-0 group">
              <div className="w-6 h-6 rounded-md bg-slate-900 text-white flex items-center justify-center font-display font-bold text-xs tracking-tight shadow-sm">
                O
              </div>
              <span className="font-display font-bold text-sm tracking-tight text-slate-900 group-hover:text-slate-700 transition-colors">
                OpenUPSC
              </span>
            </Link>

            {/* Center Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              <Link
                href="/"
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                  pathname === '/'
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`}
              >
                Home
              </Link>

              <Link
                href="/roadmaps"
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                  pathname.startsWith('/roadmaps')
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`}
              >
                Roadmap
              </Link>

              <Link
                href="/resources"
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                  pathname.startsWith('/resources')
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`}
              >
                Resources
              </Link>

              <Link
                href="/ncert"
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                  pathname.startsWith('/ncert')
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`}
              >
                NCERT
              </Link>

              {/* Logged-In User Links */}
              {isAuthenticated ? (
                <>
                  {/* Study Dropdown */}
                  <div className="relative" ref={studyRef}>
                    <button
                      type="button"
                      onClick={() => setStudyDropdownOpen(!studyDropdownOpen)}
                      className={`flex items-center gap-1 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                        isStudyActive
                          ? 'bg-slate-900 text-white shadow-subtle'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                      }`}
                    >
                      <span>Study</span>
                      <ChevronDown className="w-3 h-3 opacity-60" />
                    </button>

                    {studyDropdownOpen && (
                      <div className="absolute top-full left-0 mt-2 w-64 bg-white/95 backdrop-blur-2xl border border-slate-200/80 rounded-3xl p-2.5 shadow-command space-y-1 animate-in zoom-in-95 duration-100">
                        {studySublinks.map((sub) => (
                          <Link
                            key={sub.href}
                            href={sub.href}
                            onClick={() => setStudyDropdownOpen(false)}
                            className={`block p-2.5 rounded-2xl transition-colors ${
                              pathname === sub.href ? 'bg-slate-100 font-semibold' : 'hover:bg-slate-50'
                            }`}
                          >
                            <span className="text-xs font-medium text-slate-900 block">{sub.label}</span>
                            <span className="text-[10px] text-slate-400 font-sans block">{sub.desc}</span>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>

                  <Link
                    href="/progress"
                    className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                      pathname === '/progress'
                        ? 'bg-slate-900 text-white shadow-subtle'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                    }`}
                  >
                    Progress
                  </Link>

                  <Link
                    href="/saved"
                    className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                      pathname === '/saved'
                        ? 'bg-slate-900 text-white shadow-subtle'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                    }`}
                  >
                    Saved
                  </Link>
                </>
              ) : (
                <Link
                  href="/pyqs"
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                    pathname.startsWith('/pyqs')
                      ? 'bg-slate-900 text-white shadow-subtle'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                  }`}
                >
                  PYQs
                </Link>
              )}
            </nav>

            {/* Right Controls */}
            <div className="flex items-center gap-2">
              {/* ⌘K Command Search */}
              <button
                type="button"
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200/80 text-slate-600 text-xs font-medium transition-colors"
              >
                <Search className="w-3.5 h-3.5 text-slate-500" />
                <span className="hidden sm:inline text-[11px] text-slate-500">Search</span>
                <kbd className="hidden lg:inline-flex items-center text-[10px] text-slate-400 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
                  ⌘K
                </kbd>
              </button>

              {/* Install App Button */}
              <div className="hidden xl:block">
                <InstallAppButton />
              </div>

              {/* AUTH STATE BUTTONS */}
              {isAuthenticated ? (
                <>
                  <Link
                    href="/dashboard"
                    className={`hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      pathname === '/dashboard'
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 hover:bg-slate-200/80 text-slate-700'
                    }`}
                  >
                    <span>Dashboard</span>
                  </Link>

                  {/* Profile Dropdown Menu */}
                  <div className="relative" ref={profileRef}>
                    <button
                      type="button"
                      onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                      className={`w-7 h-7 rounded-full flex items-center justify-center font-display font-bold text-xs transition-smooth ${
                        pathname.startsWith('/profile') || profileDropdownOpen
                          ? 'bg-slate-900 text-white ring-2 ring-slate-900'
                          : 'bg-slate-900 text-white hover:bg-slate-800'
                      }`}
                      title={profile?.name || 'Account Menu'}
                    >
                      {initials}
                    </button>

                    {profileDropdownOpen && (
                      <div className="absolute top-full right-0 mt-2 w-56 bg-white/95 backdrop-blur-2xl border border-slate-200/80 rounded-3xl p-2 shadow-command space-y-1 animate-in zoom-in-95 duration-100 text-xs font-sans">
                        <div className="px-3 py-2 border-b border-slate-100">
                          <p className="font-semibold text-slate-900 line-clamp-1">{profile?.name || 'Aspirant'}</p>
                          <p className="text-[11px] text-slate-400 font-mono line-clamp-1">{user?.email || profile?.email || ''}</p>
                        </div>

                        <Link
                          href="/dashboard"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-slate-50 text-slate-700"
                        >
                          <LayoutDashboard className="w-3.5 h-3.5 text-slate-500" />
                          <span>Personal Dashboard</span>
                        </Link>

                        <Link
                          href="/profile"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-slate-50 text-slate-700"
                        >
                          <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                          <span>My Profile & Stage</span>
                        </Link>

                        <Link
                          href="/study/today"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-slate-50 text-slate-700"
                        >
                          <Calendar className="w-3.5 h-3.5 text-slate-500" />
                          <span>Today’s Plan & Timetable</span>
                        </Link>

                        <Link
                          href="/study/history"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-slate-50 text-slate-700"
                        >
                          <History className="w-3.5 h-3.5 text-slate-500" />
                          <span>Study History & Analytics</span>
                        </Link>

                        <Link
                          href="/saved"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-slate-50 text-slate-700"
                        >
                          <Bookmark className="w-3.5 h-3.5 text-slate-500" />
                          <span>Saved Resources</span>
                        </Link>

                        <Link
                          href="/settings"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-slate-50 text-slate-700"
                        >
                          <Settings className="w-3.5 h-3.5 text-slate-500" />
                          <span>Settings & Preferences</span>
                        </Link>

                        <div className="pt-1 border-t border-slate-100">
                          <button
                            type="button"
                            onClick={handleLogout}
                            className="w-full flex items-center gap-2 px-3 py-2 rounded-2xl hover:bg-rose-50 text-rose-600 transition-colors text-left"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                            <span>Log Out</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </>
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

              {/* Mobile Drawer Trigger */}
              <button
                type="button"
                onClick={() => setMobileOpen(!mobileOpen)}
                className="md:hidden p-1.5 rounded-full text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              >
                {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Dropdown Drawer */}
        {mobileOpen && (
          <div className="md:hidden max-w-6xl mx-auto mt-2 pointer-events-auto">
            <div className="bg-white/95 backdrop-blur-2xl border border-slate-200/80 rounded-3xl p-4 shadow-command space-y-2 animate-in slide-in-from-top-2 duration-150">
              <div className="grid grid-cols-2 gap-2 pt-1">
                <Link
                  href="/"
                  onClick={() => setMobileOpen(false)}
                  className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                >
                  Home
                </Link>
                <Link
                  href="/roadmaps"
                  onClick={() => setMobileOpen(false)}
                  className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                >
                  Roadmap
                </Link>
                <Link
                  href="/resources"
                  onClick={() => setMobileOpen(false)}
                  className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                >
                  Resources
                </Link>
                <Link
                  href="/ncert"
                  onClick={() => setMobileOpen(false)}
                  className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                >
                  NCERTs
                </Link>
                {isAuthenticated ? (
                  <>
                    <Link
                      href="/study"
                      onClick={() => setMobileOpen(false)}
                      className="p-3 rounded-2xl text-xs font-medium bg-slate-900 text-white text-center font-semibold"
                    >
                      Focus Timer
                    </Link>
                    <Link
                      href="/study/today"
                      onClick={() => setMobileOpen(false)}
                      className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                    >
                      Today’s Plan
                    </Link>
                    <Link
                      href="/progress"
                      onClick={() => setMobileOpen(false)}
                      className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                    >
                      Progress
                    </Link>
                    <Link
                      href="/settings"
                      onClick={() => setMobileOpen(false)}
                      className="p-3 rounded-2xl text-xs font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 text-center"
                    >
                      Settings
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      href="/auth"
                      onClick={() => setMobileOpen(false)}
                      className="p-3 rounded-2xl text-xs font-medium bg-slate-100 text-slate-900 text-center font-semibold"
                    >
                      Log in
                    </Link>
                    <Link
                      href="/auth?mode=signup"
                      onClick={() => setMobileOpen(false)}
                      className="p-3 rounded-2xl text-xs font-medium bg-slate-900 text-white text-center font-semibold"
                    >
                      Sign up
                    </Link>
                  </>
                )}
              </div>

              <div className="pt-2 border-t border-slate-100">
                <InstallAppButton className="w-full py-2.5 px-3 rounded-2xl bg-sky-50 text-sky-900 border border-sky-200/60 text-xs font-semibold flex items-center justify-center gap-2" />
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Mobile Floating Bottom Glass Navigation Bar */}
      <div className="md:hidden fixed bottom-3 left-2.5 right-2.5 z-40 bg-white/90 backdrop-blur-xl border border-white/90 shadow-floating rounded-full px-1.5 py-1 flex items-center justify-between max-w-md mx-auto">
        <Link
          href="/"
          className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1.5 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
            pathname === '/' ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <div className={`w-4 h-4 flex items-center justify-center ${pathname === '/' ? 'text-slate-900' : 'text-slate-400'}`}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </div>
          <span className="truncate">Home</span>
        </Link>
        <Link
          href="/roadmaps"
          className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1.5 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
            pathname.startsWith('/roadmaps') ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <Map className="w-4 h-4" />
          <span className="truncate">Roadmap</span>
        </Link>
        <Link
          href={isAuthenticated ? "/study" : "/resources"}
          className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1.5 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
            pathname.startsWith('/study') || pathname.startsWith('/resources') ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span className="truncate">{isAuthenticated ? "Study" : "Resources"}</span>
        </Link>
        <Link
          href={isAuthenticated ? "/progress" : "/ncert"}
          className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1.5 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
            pathname === '/progress' || pathname.startsWith('/ncert') ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span className="truncate">{isAuthenticated ? "Progress" : "NCERT"}</span>
        </Link>
        <Link
          href={isAuthenticated ? "/profile" : "/auth"}
          className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-1.5 min-h-[44px] text-[10px] font-medium active:scale-95 transition-transform ${
            pathname === '/profile' || pathname.startsWith('/auth') ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <UserIcon className="w-4 h-4" />
          <span className="truncate">{isAuthenticated ? 'Profile' : 'Log In'}</span>
        </Link>
      </div>

      <SearchCommand isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
