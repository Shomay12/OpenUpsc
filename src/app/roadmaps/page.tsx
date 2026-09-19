'use client';

import React from 'react';
import Link from 'next/link';
import { 
  ArrowRight, 
  ChevronRight,
  BookOpen,
  Map,
  Compass,
  CheckCircle2
} from 'lucide-react';
import { SUBJECT_ROADMAPS } from '../../data/subjectRoadmaps';

export default function RoadmapsOverviewPage() {
  const foundationClasses = [6, 7, 8, 9, 10, 11, 12];
  const advancedModules = [
    { title: 'Prelims Revision & Mock Analysis', desc: '15-year question trends, mapping techniques, and elimination frameworks.', href: '/pyqs?type=Prelims' },
    { title: 'Mains GS-1 to GS-4 Answer Matrices', desc: 'Syllabus micro-topics, ethical case studies, and structured 150/250 word frameworks.', href: '/pyqs?type=Mains' },
    { title: 'CSAT (Paper 2) Quantitative & Reasoning', desc: 'Curated practice problem sets and reading comprehension strategies.', href: '/resources?level=CSAT' },
    { title: 'Current Affairs Analytical Integration', desc: 'PIB releases, PRS legislative summaries, and editorial syntheses.', href: '/current-affairs' },
  ];

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">
          Learning Architecture
        </span>
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
          Syllabus Roadmaps
        </h1>
        <p className="text-sm text-slate-500 font-sans">
          A sequenced vertical progression from foundational NCERTs to core standard reference works and exam execution.
        </p>
      </div>

      {/* STAGE 1: FOUNDATION (CLASS 6-12) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              STAGE 01
            </span>
            <h2 className="font-display font-bold text-lg text-slate-900">
              NCERT Foundation
            </h2>
          </div>
          <Link
            href="/ncert"
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-900 hover:text-slate-600"
          >
            <span>All NCERTs</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <p className="text-xs text-slate-500 font-sans leading-relaxed">
          Master conceptual basics across History, Geography, Polity, Economics, and Science before touching standard references.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 pt-1">
          {foundationClasses.map((c) => (
            <Link
              key={c}
              href={`/ncert?class=${c}`}
              className="p-3.5 rounded-xl bg-slate-50/80 hover:bg-slate-100/90 border border-slate-200/60 text-center transition-smooth group"
            >
              <span className="font-mono text-xs font-bold text-slate-400 group-hover:text-slate-900 block">
                Class
              </span>
              <span className="font-display font-bold text-base text-slate-900">
                {c}
              </span>
            </Link>
          ))}
        </div>
      </div>

      {/* STAGE 2: CORE UPSC SUBJECT PATHWAYS */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white/85 backdrop-blur-xl border border-white/80 shadow-card space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              STAGE 02 · CORE
            </span>
            <h2 className="font-display font-bold text-lg text-slate-900">
              Core UPSC Disciplines
            </h2>
          </div>
        </div>

        <p className="text-xs text-slate-500 font-sans leading-relaxed">
          Connect foundational knowledge with authoritative standard reference books and syllabus checkpoints.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {SUBJECT_ROADMAPS.map((roadmap) => (
            <Link
              key={roadmap.subjectId}
              href={`/roadmaps/${roadmap.subjectId}`}
              className="p-5 rounded-xl bg-white border border-slate-200/80 hover:border-slate-300 shadow-subtle hover:shadow-sm transition-smooth group flex flex-col justify-between space-y-3"
            >
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-bold text-base text-slate-900 group-hover:text-slate-700">
                    {roadmap.subjectName}
                  </h3>
                  <span className="text-[10px] font-mono font-medium text-slate-400">
                    {roadmap.steps.length} Steps
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-sans line-clamp-2 leading-relaxed">
                  {roadmap.description}
                </p>
              </div>

              <div className="flex items-center gap-1 text-xs font-semibold text-slate-700 group-hover:text-slate-900 pt-2 border-t border-slate-100">
                <span>View pathway</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* STAGE 3: ADVANCED (PRELIMS, MAINS, CSAT, ESSAY) */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              STAGE 03
            </span>
            <h2 className="font-display font-bold text-lg text-slate-900">
              Advanced Exam Execution
            </h2>
          </div>
        </div>

        <p className="text-xs text-slate-500 font-sans leading-relaxed">
          Master exam-specific formats: Previous Year Question trends, CSAT aptitude, and answer writing.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {advancedModules.map((mod, idx) => (
            <Link
              key={idx}
              href={mod.href}
              className="p-4 rounded-xl bg-slate-50/80 hover:bg-slate-100/90 border border-slate-200/60 transition-smooth group flex flex-col justify-between space-y-2"
            >
              <div>
                <h3 className="font-display font-bold text-sm text-slate-900 group-hover:text-slate-700">
                  {mod.title}
                </h3>
                <p className="text-xs text-slate-500 font-sans leading-relaxed mt-0.5">
                  {mod.desc}
                </p>
              </div>

              <div className="flex items-center gap-1 text-xs font-semibold text-slate-700 group-hover:text-slate-900 pt-1">
                <span>Explore</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
