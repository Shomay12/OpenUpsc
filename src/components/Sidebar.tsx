'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Map,
  BookOpen,
  Layers,
  Clock,
  TrendingUp,
  Bookmark,
  Calendar,
  CheckSquare,
  History,
  Sparkles,
  FileText,
  User,
  Settings,
  LogOut,
  Search,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  onOpenSearch?: () => void;
}

export default function Sidebar({ onOpenSearch }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, profile, isAuthenticated, signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    router.push('/auth');
  };

  const displayName = profile?.name || user?.email?.split('@')[0] || 'Aspirant';
  const initial = displayName.charAt(0).toUpperCase();

  const mainLinks = [
    { href: isAuthenticated ? '/dashboard' : '/', label: 'Home / Dashboard', icon: LayoutDashboard, exact: true },
    { href: '/roadmaps', label: 'Roadmap', icon: Map },
    { href: '/resources', label: 'Resources', icon: BookOpen },
    { href: '/ncert', label: 'NCERT', icon: Layers },
    { href: '/study', label: 'Study', icon: Clock, exact: true },
    { href: '/progress', label: 'Progress', icon: TrendingUp },
    { href: '/saved', label: 'Saved', icon: Bookmark },
  ];

  const studyToolLinks = [
    { href: '/study', label: 'Focus Timer', icon: Clock, exact: true },
    { href: '/study/today', label: 'Today’s Plan', icon: Calendar },
    { href: '/study/timetable', label: 'Timetable', icon: CheckSquare },
    { href: '/study/history', label: 'Study History', icon: History },
    { href: '/current-affairs', label: 'Current Affairs', icon: Sparkles },
    { href: '/pyqs', label: 'PYQ Vault', icon: FileText },
  ];

  const isActive = (href: string, exact: boolean = false) => {
    if (exact) {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="hidden lg:flex w-60 xl:w-64 fixed inset-y-0 left-0 flex-col bg-white border-r border-slate-200/80 z-40 select-none">
      {/* Brand Header */}
      <div className="h-16 px-5 flex items-center justify-between border-b border-slate-100 flex-shrink-0">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center font-display font-extrabold text-xs shadow-sm">
            O
          </div>
          <div className="flex flex-col">
            <span className="font-display font-extrabold text-sm tracking-tight text-slate-900 group-hover:text-slate-700 transition-colors">
              OpenUPSC
            </span>
            <span className="text-[10px] text-slate-400 font-mono tracking-tight -mt-0.5">
              Workspace v2.0
            </span>
          </div>
        </Link>
      </div>

      {/* Quick Search Bar */}
      <div className="px-4 pt-3 pb-1 flex-shrink-0">
        <button
          type="button"
          onClick={onOpenSearch}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-slate-100/80 hover:bg-slate-200/80 text-slate-500 text-xs font-medium transition-colors group"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
            <span>Search syllabus...</span>
          </div>
          <kbd className="inline-flex items-center text-[10px] text-slate-400 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Scrollable Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6 scrollbar-none">
        {/* Main Section */}
        <div className="space-y-1">
          <span className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
            Navigation
          </span>
          <div className="space-y-0.5 pt-1">
            {mainLinks.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href, item.exact);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-smooth ${
                    active
                      ? 'bg-slate-900 text-white shadow-subtle font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {active && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Study Tools Section */}
        <div className="space-y-1">
          <span className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
            Study Tools
          </span>
          <div className="space-y-0.5 pt-1">
            {studyToolLinks.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href, item.exact);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-smooth ${
                    active
                      ? 'bg-slate-900 text-white shadow-subtle font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {active && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Account & Settings Panel */}
      <div className="p-3 border-t border-slate-100 flex-shrink-0 space-y-1">
        {isAuthenticated ? (
          <>
            <Link
              href="/profile"
              className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                pathname === '/profile'
                  ? 'bg-slate-100 text-slate-900 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <User className="w-4 h-4 text-slate-500" />
                <span>Profile & Stage</span>
              </div>
            </Link>

            <Link
              href="/settings"
              className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                pathname === '/settings'
                  ? 'bg-slate-100 text-slate-900 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Settings className="w-4 h-4 text-slate-500" />
                <span>Settings</span>
              </div>
            </Link>

            {/* User Account Info Strip */}
            <div className="pt-2 mt-1 border-t border-slate-100/80 flex items-center justify-between gap-2 px-2 py-1.5">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-full bg-slate-900 text-white flex items-center justify-center font-display font-bold text-xs flex-shrink-0 overflow-hidden">
                  {profile?.avatarUrl ? (
                    <img 
                      src={profile.avatarUrl} 
                      alt={displayName} 
                      className="w-full h-full object-cover" 
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    initial
                  )}
                </div>
                <div className="min-w-0 flex flex-col">
                  <span className="text-xs font-semibold text-slate-900 truncate leading-tight">
                    {displayName}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono truncate leading-tight">
                    {profile?.preparationStage || 'Foundation'}
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                title="Log out"
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </>
        ) : (
          <div className="p-1 space-y-2">
            <Link
              href="/auth"
              className="w-full flex items-center justify-center py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
            >
              Log in / Sign up
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
}
