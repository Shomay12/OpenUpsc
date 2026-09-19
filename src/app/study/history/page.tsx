'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  History, 
  Clock, 
  Calendar, 
  ArrowUpRight, 
  CheckCircle2, 
  Flame,
  Layers
} from 'lucide-react';
import { StudySession } from '../../../lib/types';
import { getLocalProgress } from '../../../lib/store';
import SeniorGuidanceBox from '../../../components/SeniorGuidanceBox';

export default function StudyHistoryPage() {
  const [sessions, setSessions] = useState<StudySession[]>([]);

  useEffect(() => {
    const progress = getLocalProgress();
    setSessions(progress.studySessions || []);
  }, []);

  const totalMinutes = sessions.reduce((acc, s) => acc + (s.durationMinutes || 0), 0);
  const totalHours = Math.floor(totalMinutes / 60);
  const remainingMins = totalMinutes % 60;

  // Minimal Weekly Chart Data
  const weeklyData = [
    { day: 'MON', time: '2h 10m', height: '65%' },
    { day: 'TUE', time: '1h 45m', height: '50%' },
    { day: 'WED', time: '3h 20m', height: '90%' },
    { day: 'THU', time: '2h 05m', height: '60%' },
    { day: 'FRI', time: '1h 30m', height: '45%' },
    { day: 'SAT', time: '3h 45m', height: '100%' },
    { day: 'SUN', time: '2h 40m', height: '75%' },
  ];

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none no-scrollbar w-full max-w-full border-b border-slate-150 pb-3">
        <Link
          href="/study"
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
        >
          Focus Timer
        </Link>
        <Link
          href="/study/today"
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
        >
          Today’s Plan
        </Link>
        <Link
          href="/study/timetable"
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
        >
          Timetable Schedule
        </Link>
        <Link
          href="/study/history"
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-semibold bg-slate-900 text-white shadow-subtle flex-shrink-0"
        >
          Session History
        </Link>
      </div>

      {/* Header */}
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          STUDY ARCHIVE
        </span>
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
          Study Session History
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 font-sans">
          A calm record of your focused study blocks and weekly consistency.
        </p>
      </div>

      {/* Weekly Minimal Visualization */}
      <div className="p-8 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              WEEKLY FOCUS
            </span>
            <h3 className="font-display font-bold text-lg text-slate-900">
              17h 05m this week
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-sans">
            Avg 2h 26m / day
          </span>
        </div>

        {/* Minimal Bar Chart */}
        <div className="flex items-end justify-between gap-2 h-36 pt-4 px-2">
          {weeklyData.map((item, idx) => (
            <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
              <span className="text-[10px] text-slate-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                {item.time}
              </span>
              <div
                className="w-full max-w-[32px] rounded-full bg-slate-900/90 group-hover:bg-slate-900 transition-all duration-500"
                style={{ height: item.height }}
              />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                {item.day}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-5 rounded-3xl bg-white border border-slate-200/80 shadow-subtle space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Recorded</span>
          <p className="font-display font-bold text-xl text-slate-900">{totalHours}h {remainingMins}m</p>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/80 shadow-subtle space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Sessions</span>
          <p className="font-display font-bold text-xl text-slate-900">{sessions.length}</p>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/80 shadow-subtle space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Most Studied</span>
          <p className="font-display font-bold text-xl text-slate-900">History</p>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/80 shadow-subtle space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Consistency</span>
          <p className="font-display font-bold text-xl text-emerald-600">7 Days</p>
        </div>
      </div>

      {/* Recent Sessions List */}
      <div className="space-y-3">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
          Completed Sessions
        </span>

        {sessions.map((sess) => (
          <div
            key={sess.id}
            className="p-5 rounded-3xl bg-white border border-slate-200/80 shadow-subtle flex items-center justify-between gap-4"
          >
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                  {sess.subject}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {sess.durationMinutes} minutes
                </span>
              </div>
              <h4 className="font-display font-bold text-sm text-slate-900">
                {sess.topic}
              </h4>
            </div>

            <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100 flex-shrink-0">
              ✓ Completed
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
