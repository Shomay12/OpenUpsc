'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Bookmark, 
  CheckCircle2, 
  Clock, 
  ArrowUpRight, 
  Search, 
  Sparkles 
} from 'lucide-react';
import { Resource } from '../../lib/types';
import { getStoredResources, getLocalProgress, saveLocalProgress } from '../../lib/store';
import ResourceCard from '../../components/ResourceCard';

export default function SavedResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [activeTab, setActiveTab] = useState<'Saved' | 'In Progress' | 'Completed'>('Saved');
  const [userProgress, setUserProgress] = useState<Record<string, number>>({});
  const [bookmarkedIds, setBookmarkedIds] = useState<string[]>([]);

  useEffect(() => {
    setResources(getStoredResources());
    const progress = getLocalProgress();
    setUserProgress(progress.progressPercentMap || {});
    setBookmarkedIds(progress.bookmarkedResourceIds || []);
  }, []);

  const handleProgressUpdate = (id: string, percent: number) => {
    const updated = { ...userProgress, [id]: percent };
    setUserProgress(updated);
    saveLocalProgress({ progressPercentMap: updated });
  };

  const handleBookmarkToggle = (id: string) => {
    let updated: string[];
    if (bookmarkedIds.includes(id)) {
      updated = bookmarkedIds.filter(item => item !== id);
    } else {
      updated = [...bookmarkedIds, id];
    }
    setBookmarkedIds(updated);
    saveLocalProgress({ bookmarkedResourceIds: updated });
  };

  const filteredResources = resources.filter((res) => {
    const pct = userProgress[res.id] || 0;
    if (activeTab === 'Saved') return bookmarkedIds.includes(res.id);
    if (activeTab === 'In Progress') return pct > 0 && pct < 100;
    if (activeTab === 'Completed') return pct === 100;
    return true;
  });

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          PERSONAL VAULT
        </span>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
          Saved Resources
        </h1>
        <p className="text-sm sm:text-base text-slate-500 font-sans">
          Your bookmarked courses, active lectures, and completed syllabus milestones.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-150 pb-4">
        {['Saved', 'In Progress', 'Completed'].map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab as any)}
            className={`px-4 py-2 rounded-full text-xs font-semibold transition-smooth ${
              activeTab === tab
                ? 'bg-slate-900 text-white shadow-subtle'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Resources Grid */}
      {filteredResources.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredResources.map((res) => (
            <ResourceCard
              key={res.id}
              resource={res}
              userProgressPercent={userProgress[res.id] || 0}
              isBookmarked={bookmarkedIds.includes(res.id)}
              onProgressUpdate={handleProgressUpdate}
              onBookmarkToggle={handleBookmarkToggle}
            />
          ))}
        </div>
      ) : (
        <div className="p-16 text-center bg-white rounded-2xl border border-slate-200/80 space-y-3">
          <p className="font-display font-bold text-slate-800 text-lg">No {activeTab.toLowerCase()} resources yet.</p>
          <p className="text-xs text-slate-400 font-sans">
            Bookmark resources while exploring the catalog and they will appear here.
          </p>
          <Link
            href="/resources"
            className="inline-flex items-center gap-1.5 px-6 py-3 rounded-full bg-slate-900 text-white text-xs font-semibold shadow-subtle"
          >
            <span>Explore Resource Library</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
