'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  CheckCircle2, 
  ArrowRight, 
  Sparkles, 
  BookOpen, 
  Clock, 
  TrendingUp,
  Flame,
  Layers
} from 'lucide-react';
import { getLocalProgress } from '../../lib/store';
import SeniorGuidanceBox from '../../components/SeniorGuidanceBox';

export default function ProgressPage() {
  const [progressState, setProgressState] = useState<any>(null);

  useEffect(() => {
    setProgressState(getLocalProgress());
  }, []);

  const subjectsProgress = [
    { name: 'NCERT Foundation (Class 6–12)', percent: 72, href: '/ncert' },
    { name: 'History (Ancient · Medieval · Modern)', percent: 64, href: '/roadmaps/history' },
    { name: 'Geography & Physical Environment', percent: 54, href: '/roadmaps/geography' },
    { name: 'Indian Polity & Constitution', percent: 31, href: '/roadmaps/polity' },
    { name: 'Economy & Indian Development', percent: 18, href: '/roadmaps/economy' },
    { name: 'Environment & Ecology', percent: 14, href: '/resources' },
    { name: 'CSAT (Paper 2)', percent: 25, href: '/resources?level=CSAT' },
  ];

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">
          Analytics & Mastery
        </span>
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
          Your Preparation
        </h1>
        <p className="text-sm text-slate-500 font-sans">
          A clear, understated view of where you stand across the syllabus.
        </p>
      </div>

      {/* Overall Progress Glass Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/85 backdrop-blur-xl border border-white/80 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">
            Overall Completion
          </span>
          <div className="font-display font-extrabold text-4xl sm:text-5xl text-slate-900 tabular-nums">
            68%
          </div>
          <p className="text-xs text-slate-500 font-sans">
            Curriculum checkpoints across foundational NCERTs and standard core syllabus.
          </p>
        </div>

        <Link
          href="/study"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm transition-smooth shrink-0"
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Resume Study Timer</span>
        </Link>
      </div>

      {/* Subject-Wise Linear Progress Breakdown */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <h2 className="font-display font-bold text-lg text-slate-900 tracking-tight">
            Syllabus Progression
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Calculated from completed resources
          </span>
        </div>

        <div className="space-y-5">
          {subjectsProgress.map((sub, idx) => (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <Link
                  href={sub.href}
                  className="font-medium text-slate-800 hover:text-slate-900 hover:underline"
                >
                  {sub.name}
                </Link>
                <span className="font-mono text-slate-500 font-medium">{sub.percent}%</span>
              </div>

              {/* Minimal Linear Bar */}
              <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-slate-900 rounded-full transition-all duration-700"
                  style={{ width: `${sub.percent}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
