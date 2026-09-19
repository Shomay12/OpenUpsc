'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { 
  Search, 
  RotateCcw, 
  ArrowUpRight, 
  Sparkles, 
  X 
} from 'lucide-react';
import { Resource, Language, StageLevel, ResourceType } from '../../lib/types';
import { getStoredResources, getLocalProgress, saveLocalProgress } from '../../lib/store';
import ResourceCard from '../../components/ResourceCard';
import SeniorGuidanceBox from '../../components/SeniorGuidanceBox';

function ResourcesContent() {
  const searchParams = useSearchParams();
  const initialCategory = searchParams.get('category') || 'All';
  const initialLevel = searchParams.get('level') || 'All';
  const initialSearch = searchParams.get('search') || '';

  const [resources, setResources] = useState<Resource[]>([]);
  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [selectedPill, setSelectedPill] = useState<string>('All');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('All');
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

  const filterPills = [
    'All',
    'NCERT',
    'History',
    'Geography',
    'Indian Polity',
    'Economy',
    'CSAT',
    'Prelims',
    'Mains',
    'Current Affairs'
  ];

  // Filtering
  const filteredResources = resources.filter((res) => {
    // Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchesTitle = res.title.toLowerCase().includes(q);
      const matchesDesc = res.description.toLowerCase().includes(q);
      const matchesSubj = res.subject.toLowerCase().includes(q);
      const matchesProvider = res.provider.toLowerCase().includes(q);
      const matchesTags = res.tags.some(t => t.toLowerCase().includes(q));
      if (!matchesTitle && !matchesDesc && !matchesSubj && !matchesProvider && !matchesTags) {
        return false;
      }
    }

    // Pill Filter
    if (selectedPill !== 'All') {
      const p = selectedPill.toLowerCase();
      const matchesSubj = res.subject.toLowerCase().includes(p);
      const matchesLevel = res.level.toLowerCase().includes(p);
      const matchesCategory = res.category.toLowerCase().includes(p);
      const matchesTags = res.tags.some(t => t.toLowerCase().includes(p));
      if (!matchesSubj && !matchesLevel && !matchesCategory && !matchesTags) {
        return false;
      }
    }

    return true;
  });

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header & Large Search Input */}
      <div className="space-y-4 max-w-3xl">
        <div className="space-y-1.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            RESOURCE EXPLORER
          </span>
          <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
            Find what you need.
          </h1>
        </div>

        {/* Large Minimal Search Box */}
        <div className="relative pt-1">
          <Search className="w-4 h-4 sm:w-5 sm:h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search History, Polity, NCERT Class 11..."
            className="w-full pl-11 pr-10 py-3 sm:py-3.5 rounded-2xl border border-slate-200/80 bg-white font-sans text-sm sm:text-base text-slate-900 placeholder:text-slate-400 shadow-subtle focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 transition-smooth"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 p-1 rounded-full text-slate-400 hover:text-slate-700"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Pills (Horizontally Scrollable on Mobile) */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none no-scrollbar w-full max-w-full">
          {filterPills.map((pill) => {
            const isSelected = selectedPill === pill;
            return (
              <button
                key={pill}
                type="button"
                onClick={() => setSelectedPill(pill)}
                className={`px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-semibold transition-smooth flex-shrink-0 ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'bg-white text-slate-600 border border-slate-200/80 hover:bg-slate-50'
                }`}
              >
                {pill}
              </button>
            );
          })}
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
          <span>Showing <strong className="text-slate-800">{filteredResources.length}</strong> resources</span>
          {(searchQuery || selectedPill !== 'All') && (
            <button
              type="button"
              onClick={() => { setSearchQuery(''); setSelectedPill('All'); }}
              className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 font-medium"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Resource Cards Grid */}
      {filteredResources.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
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
          <p className="font-display font-bold text-slate-800 text-lg">No matching resources found</p>
          <p className="text-xs text-slate-400 font-sans">
            Try adjusting your search terms or selecting a different subject pill.
          </p>
          <button
            type="button"
            onClick={() => { setSearchQuery(''); setSelectedPill('All'); }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-slate-900 text-white text-xs font-semibold shadow-subtle"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Search</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default function ResourcesPage() {
  return (
    <Suspense fallback={
      <div className="w-full max-w-[1500px] mx-auto px-4 py-32 text-center space-y-2">
        <div className="w-6 h-6 rounded-full border-2 border-slate-900 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-slate-400 font-medium">Loading Resource Library...</p>
      </div>
    }>
      <ResourcesContent />
    </Suspense>
  );
}
