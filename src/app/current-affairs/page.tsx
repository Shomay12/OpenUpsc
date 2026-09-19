'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowUpRight, 
  Clock, 
  ExternalLink
} from 'lucide-react';
import { CURRENT_AFFAIRS_CATEGORIES } from '../../data/currentAffairsData';
import SeniorGuidanceBox from '../../components/SeniorGuidanceBox';

export default function CurrentAffairsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const filteredCategories = selectedCategory === 'All' 
    ? CURRENT_AFFAIRS_CATEGORIES 
    : CURRENT_AFFAIRS_CATEGORIES.filter(c => c.id === selectedCategory);

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700">
          <span>POLICY & SCHEMES</span>
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
          Current Affairs & Policy Hub
        </h1>
        <p className="text-sm sm:text-base text-slate-500 font-sans max-w-2xl leading-relaxed">
          Avoid 4-hour daily newspaper note-making traps. Use verified government releases, legislative summaries, and targeted video debates.
        </p>
      </div>

      <SeniorGuidanceBox
        advice="Current Affairs static foundation ke bina adhoora hai. Connect every news article back to the core syllabus: Economy, Environment, Constitution, and Technology."
        title="Mentor Rule on Daily News"
      />

      {/* Routine Blueprint Container */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-4">
        <h3 className="font-display font-bold text-slate-900 text-base flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-900" />
          <span>The 60-Minute Daily Current Affairs Routine</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-150 space-y-1">
            <span className="font-bold text-slate-900 block">1. Newspaper Editorials (30m)</span>
            <p className="text-slate-500 leading-relaxed">
              Read 2–3 major policy editorials from The Hindu or Indian Express Explained.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-150 space-y-1">
            <span className="font-bold text-slate-900 block">2. Official PIB & PRS (15m)</span>
            <p className="text-slate-500 leading-relaxed">
              Scan Press Information Bureau for Cabinet decisions and PRS for bill summaries.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-150 space-y-1">
            <span className="font-bold text-slate-900 block">3. Sansad TV Debates (Weekend)</span>
            <p className="text-slate-500 leading-relaxed">
              Watch 1 episode of Sansad TV Perspective on Sunday for balanced diplomacy analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none border-b border-slate-150">
        <button
          type="button"
          onClick={() => setSelectedCategory('All')}
          className={`px-4 py-2 rounded-full text-xs font-semibold transition-smooth ${
            selectedCategory === 'All'
              ? 'bg-slate-900 text-white shadow-subtle'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All Topics
        </button>
        {CURRENT_AFFAIRS_CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-4 py-2 rounded-full text-xs font-semibold transition-smooth flex-shrink-0 ${
              selectedCategory === cat.id
                ? 'bg-slate-900 text-white shadow-subtle'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {cat.title.split('(')[0]}
          </button>
        ))}
      </div>

      {/* Categorized Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filteredCategories.map((cat) => (
          <div
            key={cat.id}
            className="p-6 sm:p-7 rounded-2xl bg-white border border-slate-200/80 shadow-card flex flex-col justify-between space-y-6"
          >
            <div className="space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {cat.gsPaper}
                </span>
                <h3 className="font-display font-bold text-slate-900 text-lg sm:text-xl">
                  {cat.title}
                </h3>
                <p className="text-xs text-slate-500 font-sans">
                  {cat.description}
                </p>
              </div>

              {/* Free Legitimate Sources List */}
              <div className="space-y-2 pt-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                  Official & Free Portals
                </span>
                <div className="space-y-2">
                  {cat.keySources.map((source, sIdx) => (
                    <div
                      key={sIdx}
                      className="p-3.5 rounded-xl bg-slate-50 border border-slate-150 space-y-0.5 text-xs font-sans"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900">{source.name}</span>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900"
                        >
                          <span>Open</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </a>
                      </div>
                      <p className="text-[11px] text-slate-400">{source.howToUse}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sub-topics */}
              <div className="pt-2 flex flex-wrap gap-1.5">
                {cat.highYieldTopics.map((t, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <Link
                href="/roadmaps"
                className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition-smooth"
              >
                <span>View Static Subject Roadmap</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
