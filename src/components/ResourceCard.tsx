'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowUpRight, 
  Bookmark, 
  BookmarkCheck, 
  Edit3, 
  Clock, 
  ShieldCheck,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import { Resource, VerificationStatus } from '../lib/types';
import ProgressBadge from './ProgressBadge';
import NotesModal from './NotesModal';

interface ResourceCardProps {
  resource: Resource;
  userProgressPercent?: number;
  isBookmarked?: boolean;
  onProgressUpdate?: (resourceId: string, percent: number) => void;
  onBookmarkToggle?: (resourceId: string) => void;
  showClassBadge?: boolean;
}

export default function ResourceCard({
  resource,
  userProgressPercent = 0,
  isBookmarked = false,
  onProgressUpdate,
  onBookmarkToggle,
  showClassBadge = true
}: ResourceCardProps) {
  const [notesOpen, setNotesOpen] = useState(false);

  return (
    <>
      <div className={`p-5 rounded-2xl bg-white border transition-smooth group flex flex-col justify-between ${
        userProgressPercent === 100 
          ? 'border-emerald-200 bg-emerald-50/10' 
          : 'border-slate-200/80 hover:border-slate-300 shadow-subtle hover:shadow-card'
      }`}>
        {/* Card Header & Content */}
        <div className="space-y-3">
          {/* Top Category & Bookmark */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400 font-mono">
                {resource.subject}
              </span>
              {resource.classLevel && showClassBadge && (
                <span className="text-[10px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
                  {resource.classLevel}
                </span>
              )}
            </div>

            <div className="flex items-center gap-1">
              {resource.verificationStatus === 'Verified' && (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                  <ShieldCheck className="w-3 h-3 text-emerald-600" />
                  <span>Verified</span>
                </span>
              )}
              {onBookmarkToggle && (
                <button
                  type="button"
                  onClick={() => onBookmarkToggle(resource.id)}
                  className="p-1 rounded text-slate-400 hover:text-slate-900 transition-colors"
                  title={isBookmarked ? 'Remove bookmark' : 'Save resource'}
                >
                  {isBookmarked ? (
                    <BookmarkCheck className="w-3.5 h-3.5 text-slate-900 fill-slate-900" />
                  ) : (
                    <Bookmark className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Title & Type */}
          <div className="space-y-0.5">
            <h3 className="font-display font-bold text-sm sm:text-base text-slate-900 leading-snug tracking-tight">
              {resource.title}
            </h3>
            <p className="text-[11px] text-slate-400 font-medium">
              {resource.provider} · {resource.type} {resource.estimatedHours > 0 && `· ~${resource.estimatedHours}h`}
            </p>
          </div>

          {/* Short Description */}
          <p className="text-xs text-slate-600 font-sans leading-relaxed line-clamp-2">
            {resource.description}
          </p>

          {/* Metadata */}
          <div className="text-[10px] text-slate-400 flex items-center gap-2 pt-0.5 font-mono">
            <span>{resource.language}</span>
            {resource.verificationSignals?.views && (
              <>
                <span>·</span>
                <span>{resource.verificationSignals.views} views</span>
              </>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 mt-3 border-t border-slate-100 flex flex-col gap-2.5">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium text-slate-400 font-mono">Progress:</span>
              {onProgressUpdate && (
                <ProgressBadge
                  itemId={resource.id}
                  currentPercent={userProgressPercent}
                  onUpdate={(pct) => onProgressUpdate(resource.id, pct)}
                  size="sm"
                />
              )}
            </div>

            <button
              type="button"
              onClick={() => setNotesOpen(true)}
              className="inline-flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-900 font-medium"
            >
              <Edit3 className="w-3 h-3" />
              <span>Notes</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/study?subject=${encodeURIComponent(resource.subject)}&topic=${encodeURIComponent(resource.title)}&resourceId=${encodeURIComponent(resource.id)}&duration=50`}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs transition-smooth"
            >
              <Clock className="w-3 h-3" />
              <span>Study</span>
            </Link>

            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-sm transition-smooth group/btn"
            >
              <span>{resource.type === 'PDF' ? 'Official PDF' : 'Open'}</span>
              <ArrowUpRight className="w-3 h-3 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
            </a>
          </div>
        </div>
      </div>

      <NotesModal
        isOpen={notesOpen}
        onClose={() => setNotesOpen(false)}
        itemId={resource.id}
        itemTitle={resource.title}
        itemCategory={resource.subject}
      />
    </>
  );
}
