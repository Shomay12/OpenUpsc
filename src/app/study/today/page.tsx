'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  Play, 
  CheckCircle2, 
  Clock, 
  Calendar, 
  Plus, 
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { TimetableEvent } from '../../../lib/types';
import { getLocalProgress, saveLocalProgress } from '../../../lib/store';
import SeniorGuidanceBox from '../../../components/SeniorGuidanceBox';

export default function TodayPlanPage() {
  const router = useRouter();
  const [timetable, setTimetable] = useState<TimetableEvent[]>([]);

  useEffect(() => {
    const progress = getLocalProgress();
    setTimetable(progress.timetable || []);
  }, []);

  const toggleComplete = (id: string) => {
    const updated = timetable.map((item) => {
      if (item.id === id) {
        return { ...item, completed: !item.completed };
      }
      return item;
    });
    setTimetable(updated);
    saveLocalProgress({ timetable: updated });
  };

  const startSession = (item: TimetableEvent) => {
    router.push(`/study?subject=${encodeURIComponent(item.subject)}&topic=${encodeURIComponent(item.topic)}&duration=50`);
  };

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
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-semibold bg-slate-900 text-white shadow-subtle flex-shrink-0"
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
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
        >
          Session History
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            DAILY TIMELINE
          </span>
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
            Today’s Study Schedule
          </h1>
        </div>

        <Link
          href="/study/timetable"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Edit Timetable</span>
        </Link>
      </div>

      <SeniorGuidanceBox
        advice="Stick to 3 deep blocks of 50 minutes each rather than a chaotic 10-hour day. Consistency over intensity."
        title="Senior Time Management"
      />

      {/* Vertical Timeline View */}
      {timetable.length > 0 ? (
        <div className="space-y-4 relative before:absolute before:inset-0 before:left-5 before:w-0.5 before:bg-slate-150 pl-4 sm:pl-6">
          {timetable.map((item, idx) => (
            <div
              key={item.id}
              className={`p-6 rounded-3xl border transition-smooth relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                item.completed
                  ? 'bg-emerald-50/20 border-emerald-200/80 shadow-subtle'
                  : 'bg-white border-slate-200/80 shadow-card hover:shadow-cardHover'
              }`}
            >
              <div className="flex items-start gap-4">
                <button
                  type="button"
                  onClick={() => toggleComplete(item.id)}
                  className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors ${
                    item.completed
                      ? 'bg-emerald-600 text-white'
                      : 'border-2 border-slate-300 hover:border-slate-500'
                  }`}
                >
                  {item.completed && <CheckCircle2 className="w-4 h-4" />}
                </button>

                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-slate-400">
                      {item.startTime} – {item.endTime}
                    </span>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                      {item.subject}
                    </span>
                  </div>
                  <h3 className={`font-display font-bold text-base sm:text-lg tracking-tight ${
                    item.completed ? 'text-slate-400 line-through' : 'text-slate-900'
                  }`}>
                    {item.topic}
                  </h3>
                  {item.resourceTitle && (
                    <p className="text-xs text-slate-400 font-sans">
                      Resource: {item.resourceTitle}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                {!item.completed && (
                  <button
                    type="button"
                    onClick={() => startSession(item)}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-subtle transition-smooth"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Start Session</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-16 text-center bg-white rounded-4xl border border-slate-200/80 space-y-4">
          <p className="font-display font-bold text-slate-800 text-lg">Your study plan is empty.</p>
          <p className="text-xs text-slate-400 font-sans">
            Create recurring study blocks to organize your preparation day.
          </p>
          <Link
            href="/study/timetable"
            className="inline-flex items-center gap-1.5 px-6 py-3 rounded-full bg-slate-900 text-white text-xs font-semibold shadow-subtle"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Timetable Schedule</span>
          </Link>
        </div>
      )}
    </div>
  );
}
