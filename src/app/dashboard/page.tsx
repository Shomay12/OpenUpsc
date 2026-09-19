'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ArrowRight, 
  ArrowUpRight, 
  BookOpen, 
  Bookmark, 
  Clock, 
  Calendar, 
  Play, 
  Layers, 
  TrendingUp, 
  CheckCircle2, 
  Sparkles,
  ChevronRight,
  Target,
  Flame,
  FileText
} from 'lucide-react';
import { UserProgressState, Resource, TimetableEvent } from '../../lib/types';
import { getLocalProgress, saveLocalProgress, getStoredResources } from '../../lib/store';
import ResourceCard from '../../components/ResourceCard';
import NotesModal from '../../components/NotesModal';
import { useAuth } from '../../context/AuthContext';

export default function DashboardPage() {
  const { user, profile } = useAuth();
  const [progressState, setProgressState] = useState<UserProgressState | null>(null);
  const [resources, setResources] = useState<Resource[]>([]);
  const [notesModalData, setNotesModalData] = useState<{ id: string; title: string; category: string } | null>(null);

  useEffect(() => {
    setProgressState(getLocalProgress());
    setResources(getStoredResources());
  }, []);

  const refreshState = () => {
    setProgressState(getLocalProgress());
  };

  const handleBookmarkToggle = (id: string) => {
    const current = getLocalProgress();
    let updated: string[];
    if (current.bookmarkedResourceIds.includes(id)) {
      updated = current.bookmarkedResourceIds.filter(item => item !== id);
    } else {
      updated = [...current.bookmarkedResourceIds, id];
    }
    saveLocalProgress({ bookmarkedResourceIds: updated });
    refreshState();
  };

  if (!progressState) return null;

  const displayName = profile?.name || user?.email?.split('@')[0] || 'Aspirant';
  const firstName = displayName.split(' ')[0];
  const bookmarkedResources = resources.filter(r => progressState.bookmarkedResourceIds?.includes(r.id));
  const timetable = progressState.timetable || [];
  const sessions = progressState.studySessions || [];

  // Calculate today's study minutes
  const todayStr = new Date().toISOString().split('T')[0];
  const todaySessions = sessions.filter(s => s.startTime?.startsWith(todayStr) || s.createdAt?.startsWith(todayStr));
  const todayMinutes = todaySessions.reduce((acc, s) => acc + (s.durationMinutes || 0), 0) || 152;
  const targetMinutes = (profile?.dailyTargetHours || 4) * 60;
  const todayProgressPercent = Math.min(100, Math.round((todayMinutes / targetMinutes) * 100));

  // Calculate weekly study minutes (last 7 days)
  const weeklyMinutes = sessions.reduce((acc, s) => acc + (s.durationMinutes || 0), 0) || 882;

  const learningLevels = [
    { step: '01', title: 'NCERT Foundation', range: 'Class 6–10', href: '/ncert?class=6', badge: 'NCERT' },
    { step: '02', title: 'Senior Secondary', range: 'Class 11–12', href: '/ncert?class=11', badge: 'Foundation' },
    { step: '03', title: 'Core UPSC Subjects', range: 'Standard Books', href: '/roadmaps', badge: 'Core' },
    { step: '04', title: 'Current Affairs', range: 'PIB & Editorials', href: '/current-affairs', badge: 'Advanced' },
    { step: '05', title: 'PYQ Vault', range: 'Prelims + Mains', href: '/pyqs', badge: 'Execution' },
  ];

  return (
    <div className="w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200 select-none">
      {/* ================= COMPACT DASHBOARD HEADER ================= */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 pb-2 border-b border-slate-150">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              ACTIVE WORKSPACE · {profile?.preparationStage || 'FOUNDATION'}
            </span>
          </div>
          <h1 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900 tracking-tight">
            Good morning, {firstName}.
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 font-sans">
            Continue your daily preparation and complete your scheduled blocks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/study"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm transition-smooth"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>Launch Timer</span>
          </Link>
          <Link
            href="/study/timetable"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs border border-slate-200 shadow-sm transition-smooth"
          >
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span className="hidden sm:inline">Manage Timetable</span>
          </Link>
        </div>
      </div>

      {/* ================= TOP APPLICATION GRID (CONTINUE LEARNING + TODAY'S PROGRESS) ================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Continue Learning Panel (7 Cols) */}
        <div className="lg:col-span-7 p-6 sm:p-7 rounded-2xl bg-white border border-slate-200/90 shadow-subtle flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-900" />
                CONTINUE LEARNING
              </span>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                Chapter 3 of 12
              </span>
            </div>

            <div className="space-y-1">
              <h2 className="font-display font-bold text-xl sm:text-2xl text-slate-900 tracking-tight">
                Modern Indian History
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 font-sans">
                British Expansion & Administrative Policies (1757–1857) · Spectrum Reference Chapter
              </p>
            </div>

            {/* Progress percentage bar */}
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between text-xs font-sans">
                <span className="text-slate-500">Module Completion</span>
                <span className="font-mono font-bold text-slate-900">68%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-slate-900 rounded-full transition-all duration-500" style={{ width: '68%' }} />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <span className="text-xs text-slate-400 font-sans">
              Next: Subordinate Isolation & Doctrine of Lapse
            </span>
            <Link
              href="/study?subject=History&topic=Modern%20Indian%20History%20(British%20Expansion)&duration=50"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm transition-smooth"
            >
              <span>Continue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Right: Today's Progress Metrics (5 Cols) */}
        <div className="lg:col-span-5 p-6 sm:p-7 rounded-2xl bg-white border border-slate-200/90 shadow-subtle flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                TODAY’S PROGRESS
              </span>
              <span className="text-xs font-bold text-emerald-600 font-mono">
                {todayProgressPercent}% of Daily Target
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-1">
              <div className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-0.5">
                <span className="text-[10px] font-mono text-slate-400 block uppercase">Time Studied</span>
                <div className="font-display font-extrabold text-2xl text-slate-900 tabular-nums">
                  {Math.floor(todayMinutes / 60)}h {todayMinutes % 60}m
                </div>
                <span className="text-[10px] text-slate-500 font-sans">Goal: {profile?.dailyTargetHours || 4} hours</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-0.5">
                <span className="text-[10px] font-mono text-slate-400 block uppercase">This Week</span>
                <div className="font-display font-extrabold text-2xl text-slate-900 tabular-nums">
                  {Math.floor(weeklyMinutes / 60)}h {weeklyMinutes % 60}m
                </div>
                <span className="text-[10px] text-slate-500 font-sans">7-day total</span>
              </div>
            </div>

            {/* Target Horizon & Stage */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/60 border border-slate-200/50 text-xs">
              <span className="text-slate-500 font-medium">Target Exam Horizon</span>
              <span className="font-mono font-bold text-slate-900">UPSC CSE {profile?.targetAttemptYear || '2028'}</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <span className="text-xs text-slate-400 font-sans">Consistency Streak: 5 Days</span>
            <Link
              href="/study/history"
              className="inline-flex items-center gap-1 text-xs font-semibold text-slate-900 hover:text-slate-600 transition-colors"
            >
              <span>View logs</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* ================= TODAY'S STUDY PLAN / TIMETABLE SECTION ================= */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              SCHEDULE
            </span>
            <h3 className="font-display font-bold text-lg text-slate-900">
              Today’s Study Plan
            </h3>
          </div>
          <Link
            href="/study/today"
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-900 hover:text-slate-600"
          >
            <span>Full Timeline</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Dense Table/List of Today's Scheduled Blocks */}
        <div className="space-y-2.5">
          {timetable.length > 0 ? (
            timetable.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="p-3.5 sm:p-4 rounded-xl bg-slate-50/70 border border-slate-200/60 hover:border-slate-300 transition-smooth flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono text-xs font-bold text-slate-800 bg-white px-2.5 py-1 rounded-lg border border-slate-200 flex-shrink-0">
                    {item.startTime}
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-bold text-sm text-slate-900 truncate">{item.subject}</span>
                      {item.completed && (
                        <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          ✓ Completed
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 font-sans truncate">{item.topic || 'General study block'}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center flex-shrink-0">
                  <span className="text-xs font-mono text-slate-400">60 min</span>
                  <Link
                    href={`/study?subject=${encodeURIComponent(item.subject)}&topic=${encodeURIComponent(item.topic || '')}&duration=50`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-smooth"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    <span>Start</span>
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200/60 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-mono text-xs font-bold text-slate-800">09:00 - 10:30</span>
                  <p className="text-xs font-semibold text-slate-900">Modern History (British Expansion)</p>
                </div>
                <Link
                  href="/study?subject=History&duration=50"
                  className="px-3 py-1 rounded-lg bg-slate-900 text-white text-xs font-medium"
                >
                  Start
                </Link>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200/60 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-mono text-xs font-bold text-slate-800">11:00 - 12:30</span>
                  <p className="text-xs font-semibold text-slate-900">Indian Polity (Preamble & Rights)</p>
                </div>
                <Link
                  href="/study?subject=Polity&duration=50"
                  className="px-3 py-1 rounded-lg bg-slate-900 text-white text-xs font-medium"
                >
                  Start
                </Link>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200/60 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-mono text-xs font-bold text-slate-800">18:00 - 19:00</span>
                  <p className="text-xs font-semibold text-slate-900">Current Affairs Analysis (The Hindu)</p>
                </div>
                <Link
                  href="/current-affairs"
                  className="px-3 py-1 rounded-lg bg-slate-900 text-white text-xs font-medium"
                >
                  Start
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ================= 2-COLUMN SECTION: SYLLABUS PROGRESS & ROADMAP PROGRESSION ================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Syllabus Mastery (6 Cols) */}
        <div className="lg:col-span-6 p-6 sm:p-7 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                MASTERY
              </span>
              <h3 className="font-display font-bold text-base text-slate-900">
                Syllabus Progress
              </h3>
            </div>
            <Link href="/progress" className="text-xs font-semibold text-slate-900 hover:text-slate-600 inline-flex items-center gap-1">
              <span>Detailed audit</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-4 text-xs font-sans">
            <div className="space-y-1.5">
              <div className="flex justify-between text-slate-700 font-medium">
                <span>History (Ancient + Modern + Art & Culture)</span>
                <span className="font-mono font-bold text-slate-900">72%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-slate-900 rounded-full" style={{ width: '72%' }} />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-slate-700 font-medium">
                <span>Geography (Physical + Indian + Human)</span>
                <span className="font-mono font-bold text-slate-900">54%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-slate-900 rounded-full" style={{ width: '54%' }} />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-slate-700 font-medium">
                <span>Indian Polity & Governance</span>
                <span className="font-mono font-bold text-slate-900">31%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-slate-900 rounded-full" style={{ width: '31%' }} />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-slate-700 font-medium">
                <span>Indian Economy & Development</span>
                <span className="font-mono font-bold text-slate-900">45%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-slate-900 rounded-full" style={{ width: '45%' }} />
              </div>
            </div>
          </div>
        </div>

        {/* Right: Academic Roadmap Hierarchy (6 Cols) */}
        <div className="lg:col-span-6 p-6 sm:p-7 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                PATHWAYS
              </span>
              <h3 className="font-display font-bold text-base text-slate-900">
                Structured Learning Roadmap
              </h3>
            </div>
            <Link href="/roadmaps" className="text-xs font-semibold text-slate-900 hover:text-slate-600 inline-flex items-center gap-1">
              <span>View all stages</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-2">
            {learningLevels.map((lvl) => (
              <Link
                key={lvl.step}
                href={lvl.href}
                className="p-2.5 sm:p-3 rounded-xl bg-slate-50/70 hover:bg-slate-100/90 border border-slate-200/60 transition-smooth flex items-center justify-between gap-3 group"
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-lg bg-white border border-slate-200 flex items-center justify-center font-mono text-[11px] font-bold text-slate-700 flex-shrink-0">
                    {lvl.step}
                  </span>
                  <div>
                    <span className="text-xs font-bold text-slate-900 group-hover:text-slate-700 block">
                      {lvl.title}
                    </span>
                    <span className="text-[11px] text-slate-400 font-sans block">{lvl.range}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600">
                    {lvl.badge}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-700 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* ================= SAVED RESOURCES (IF ANY) ================= */}
      {bookmarkedResources.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                LIBRARY
              </span>
              <h2 className="font-display font-bold text-lg text-slate-900 tracking-tight">
                Saved Resources ({bookmarkedResources.length})
              </h2>
            </div>
            <Link
              href="/saved"
              className="inline-flex items-center gap-1 text-xs font-semibold text-slate-900 hover:text-slate-600"
            >
              <span>View all bookmarks</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {bookmarkedResources.slice(0, 3).map((res) => (
              <ResourceCard
                key={res.id}
                resource={res}
                isBookmarked={true}
                onBookmarkToggle={() => handleBookmarkToggle(res.id)}
                userProgressPercent={progressState.progressPercentMap?.[res.id] || 0}
                onProgressUpdate={(id, pct) => {
                  const updated = { ...progressState.progressPercentMap, [id]: pct };
                  saveLocalProgress({ progressPercentMap: updated });
                  refreshState();
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Notes Modal */}
      {notesModalData && (
        <NotesModal
          itemId={notesModalData.id}
          itemTitle={notesModalData.title}
          itemCategory={notesModalData.category}
          isOpen={Boolean(notesModalData)}
          onClose={() => setNotesModalData(null)}
        />
      )}
    </div>
  );
}
