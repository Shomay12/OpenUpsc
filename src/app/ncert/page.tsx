'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { 
  BookOpen, 
  Clock, 
  ExternalLink, 
  ArrowUpRight, 
  FileText, 
  Video, 
  CheckCircle2, 
  ArrowRight, 
  Edit3, 
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Layers,
  Sparkles,
  Play
} from 'lucide-react';
import { NCERT_DATA, NCERT_CLASSES } from '../../data/ncertData';
import { NCERTSubjectBook } from '../../lib/types';
import ProgressBadge from '../../components/ProgressBadge';
import NotesModal from '../../components/NotesModal';
import SeniorGuidanceBox from '../../components/SeniorGuidanceBox';
import { getLocalProgress, saveLocalProgress } from '../../lib/store';

function NCERTFoundationContent() {
  const searchParams = useSearchParams();
  const initialClass = Number(searchParams.get('class')) || 6;
  const [selectedClass, setSelectedClass] = useState<number>(initialClass);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [userProgress, setUserProgress] = useState<Record<string, number>>({});
  const [notesModalData, setNotesModalData] = useState<{ id: string; title: string; category: string } | null>(null);
  const [suggestModalChapter, setSuggestModalChapter] = useState<{ chapterNum: number; title: string; subject: string } | null>(null);
  const [suggestSuccess, setSuggestSuccess] = useState<boolean>(false);

  useEffect(() => {
    const classFromQuery = Number(searchParams.get('class'));
    if (classFromQuery && NCERT_CLASSES.includes(classFromQuery as any)) {
      setSelectedClass(classFromQuery);
    }
  }, [searchParams]);

  useEffect(() => {
    const stored = getLocalProgress();
    setUserProgress(stored.progressPercentMap || {});
  }, []);

  const classBooks = NCERT_DATA.filter((b) => b.classNum === selectedClass);
  const activeBook = classBooks.find((b) => b.id === selectedSubjectId) || classBooks[0];

  const handleProgressUpdate = (id: string, percent: number) => {
    const updated = { ...userProgress, [id]: percent };
    setUserProgress(updated);
    saveLocalProgress({ progressPercentMap: updated });
  };

  // Calculate curriculum vs resource stats for active class
  const totalSubjects = classBooks.length;
  const totalChapters = classBooks.reduce((acc, b) => acc + b.chapters.length, 0);
  const chaptersWithResources = classBooks.reduce(
    (acc, b) => acc + b.chapters.filter((c) => c.hasResources !== false).length,
    0
  );
  const classResourceCoveragePercent = totalChapters > 0 ? Math.round((chaptersWithResources / totalChapters) * 100) : 0;

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700">
          <Layers className="w-3.5 h-3.5 text-slate-900" />
          <span>CURRICULUM-FIRST ACADEMIC ARCHITECTURE</span>
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
          NCERT Foundation
        </h1>
        <p className="text-sm sm:text-base text-slate-500 font-sans max-w-2xl leading-relaxed">
          The complete academic syllabus of NCERT from Class 6 through 12. Curriculum structure is independent of resource availability.
        </p>
      </div>

      {/* Class Selector Segmented Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none border-b border-slate-150">
        {NCERT_CLASSES.map((c) => {
          const isSelected = selectedClass === c;
          return (
            <button
              key={c}
              type="button"
              onClick={() => {
                setSelectedClass(c);
                setSelectedSubjectId('');
              }}
              className={`px-4 sm:px-5 py-2 rounded-full text-xs font-semibold transition-smooth flex-shrink-0 ${
                isSelected
                  ? 'bg-slate-900 text-white shadow-subtle'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Class {c}
            </button>
          );
        })}
      </div>

      {/* Class Academic Map & Subject Coverage Summary Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              CLASS {selectedClass} FOUNDATION OVERVIEW
            </span>
            <h2 className="font-display font-bold text-xl sm:text-2xl text-slate-900">
              Curriculum & Resource Coverage
            </h2>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Curriculum Chapters</span>
              <span className="font-display font-bold text-slate-900 text-sm">{totalChapters} Chapters</span>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Resource Coverage</span>
              <span className="font-display font-bold text-slate-900 text-sm">{chaptersWithResources}/{totalChapters} ({classResourceCoveragePercent}%)</span>
            </div>
          </div>
        </div>

        {/* Consistent Subjects Grid for This Class */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {classBooks.map((b) => {
            const isSelected = activeBook?.id === b.id;
            const subjectChaptersCount = b.chapters.length;
            const subjectWithResourcesCount = b.chapters.filter(c => c.hasResources !== false).length;
            const coveragePct = subjectChaptersCount > 0 ? Math.round((subjectWithResourcesCount / subjectChaptersCount) * 100) : 0;

            let coverageBadge = {
              text: `${coveragePct}% Coverage`,
              color: 'bg-emerald-50 text-emerald-800 border-emerald-200/60',
              icon: '✓'
            };

            if (coveragePct === 100) {
              coverageBadge = { text: '100% Resource Coverage', color: 'bg-emerald-50 text-emerald-800 border-emerald-200/60', icon: '✓' };
            } else if (coveragePct > 0) {
              coverageBadge = { text: `${subjectWithResourcesCount}/${subjectChaptersCount} Chapters (${coveragePct}%)`, color: 'bg-amber-50 text-amber-800 border-amber-200/60', icon: '◐' };
            } else {
              coverageBadge = { text: 'Resources Unavailable', color: 'bg-slate-100 text-slate-600 border-slate-200', icon: '—' };
            }

            return (
              <button
                key={b.id}
                type="button"
                onClick={() => setSelectedSubjectId(b.id)}
                className={`p-4 rounded-2xl text-left border transition-smooth space-y-3 relative ${
                  isSelected
                    ? 'bg-slate-900 text-white border-slate-900 shadow-card'
                    : 'bg-slate-50/70 hover:bg-slate-100/80 text-slate-900 border-slate-200/70'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className={`font-display font-bold text-sm tracking-tight ${isSelected ? 'text-white' : 'text-slate-900'}`}>
                      {b.subjectName}
                    </h3>
                    <p className={`text-[11px] line-clamp-1 font-sans ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                      {b.bookTitle}
                    </p>
                  </div>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                    isSelected ? 'bg-white/10 text-white border-white/20' : 'bg-white text-slate-700 border-slate-200'
                  }`}>
                    {b.upscRelevance || 'High'} Relevance
                  </span>
                </div>

                <div className="pt-1">
                  <div className={`text-[10px] font-medium inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${
                    isSelected ? 'bg-white/15 text-white border-white/20' : coverageBadge.color
                  }`}>
                    <span>{coverageBadge.icon}</span>
                    <span>{coverageBadge.text}</span>
                  </div>
                </div>

                <div className={`text-[10px] ${isSelected ? 'text-slate-400' : 'text-slate-400'} pt-1`}>
                  {subjectChaptersCount} Chapters in NCERT
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Subject Navigation Horizontal Tabs */}
      {classBooks.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap pt-2">
          {classBooks.map((b) => {
            const isActive = activeBook?.id === b.id;
            const pct = userProgress[b.id] || 0;
            return (
              <button
                key={b.id}
                type="button"
                onClick={() => setSelectedSubjectId(b.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold transition-smooth ${
                  isActive
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'bg-white border border-slate-200/80 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span>{b.subjectName}</span>
                {pct > 0 && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {pct}%
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Selected Subject & Book Main Card */}
      {activeBook && (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* Main Book Surface Container */}
          <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-8">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-slate-150">
              <div className="space-y-2 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[10px] font-semibold text-slate-700 uppercase tracking-wider">
                    Class {activeBook.classNum} · {activeBook.subjectName}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-900 text-white text-[10px] font-semibold">
                    {activeBook.readingPriority} Priority
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800 text-[10px] font-medium border border-slate-200">
                    UPSC Relevance: {activeBook.upscRelevance || 'High'}
                  </span>
                </div>
                <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900">
                  {activeBook.bookTitle}
                </h2>
                <p className="text-xs sm:text-sm text-slate-600 font-sans leading-relaxed">
                  {activeBook.whyItMatters}
                </p>
              </div>

              {/* Action Buttons & Time */}
              <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-3 flex-shrink-0">
                <div className="flex items-center gap-1.5 text-xs text-slate-500 font-sans">
                  <Clock className="w-3.5 h-3.5" />
                  <span>~{activeBook.estimatedHours} hours total</span>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={activeBook.officialPdfUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-slate-200 hover:bg-slate-50 text-slate-800 text-xs font-semibold shadow-subtle transition-smooth"
                  >
                    <FileText className="w-3.5 h-3.5 text-slate-600" />
                    <span>Official NCERT PDF</span>
                    <ExternalLink className="w-3 h-3 text-slate-400" />
                  </a>

                  <Link
                    href={`/study?subject=${encodeURIComponent(activeBook.subjectName)}&topic=${encodeURIComponent(activeBook.bookTitle)}&duration=50`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Start Studying</span>
                  </Link>

                  <button
                    type="button"
                    onClick={() => setNotesModalData({ id: activeBook.id, title: activeBook.bookTitle, category: activeBook.subjectName })}
                    className="p-2 rounded-full border border-slate-200 hover:bg-slate-50 text-slate-700 transition-smooth"
                    title="Open Notes"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Verified Foundation Lecture Banner if available */}
            {activeBook.recommendedLectureUrl ? (
              <div className="p-4 sm:p-5 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Video className="w-4 h-4 text-rose-500" />
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700">
                      RECOMMENDED FOUNDATION VIDEO PLAYLIST
                    </span>
                  </div>
                  <h3 className="text-xs sm:text-sm font-semibold text-slate-900">
                    {activeBook.recommendedLectureTitle}
                  </h3>
                  <p className="text-[11px] text-slate-500 font-sans">
                    By {activeBook.recommendedLectureChannel} • {activeBook.verificationSignal}
                  </p>
                </div>

                <a
                  href={activeBook.recommendedLectureUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth flex-shrink-0"
                >
                  <span>Open Video</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-slate-50/60 border border-dashed border-slate-200 flex items-center justify-between gap-4 text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-slate-400" />
                  <span>Verified playlist currently in curation for this textbook. Use official PDF below.</span>
                </div>
                <button
                  type="button"
                  onClick={() => setSuggestModalChapter({ chapterNum: 0, title: activeBook.bookTitle, subject: activeBook.subjectName })}
                  className="text-[11px] font-semibold text-slate-800 hover:underline"
                >
                  Suggest Resource
                </button>
              </div>
            )}

            {/* Senior Aspirant Hinglish Guidance */}
            <SeniorGuidanceBox advice={activeBook.seniorHinglishAdvice} />

            {/* 2-Column Comparison: What to Focus on vs What to Skip */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-150 space-y-2">
                <span className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  What to Focus on for UPSC
                </span>
                <p className="text-slate-600 font-sans leading-relaxed">
                  {activeBook.whatToFocusOn}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-150 space-y-2">
                <span className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  What to Skip / Ignore
                </span>
                <p className="text-slate-600 font-sans leading-relaxed">
                  {activeBook.whatToSkip || 'Skip end-of-chapter elementary classroom activities, fill-in-the-blanks, and non-conceptual trivia.'}
                </p>
              </div>
            </div>

            {/* Chapter Breakdown Header */}
            <div className="pt-4 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display font-bold text-base sm:text-lg text-slate-900">
                    NCERT Chapter Breakdown
                  </h3>
                  <p className="text-xs text-slate-500 font-sans">
                    Complete curriculum chapter sequence with UPSC priority tags and resource states.
                  </p>
                </div>
                <span className="text-xs text-slate-400 font-medium font-sans">
                  {activeBook.chapters.length} Chapters in Curriculum
                </span>
              </div>

              {/* Chapter Cards List */}
              <div className="space-y-3">
                {activeBook.chapters.map((ch) => {
                  const hasResource = ch.hasResources !== false;
                  let badgeColor = 'bg-slate-100 text-slate-700';
                  if (ch.priority === 'Must Read') badgeColor = 'bg-slate-900 text-white font-semibold';
                  if (ch.priority === 'Important') badgeColor = 'bg-slate-200 text-slate-800 font-semibold';
                  if (ch.priority === 'Selective') badgeColor = 'bg-slate-100 text-slate-600';
                  if (ch.priority === 'Can Skip') badgeColor = 'bg-slate-50 text-slate-400';

                  return (
                    <div
                      key={ch.number}
                      className="p-4 sm:p-5 rounded-2xl bg-slate-50/70 border border-slate-200/70 hover:border-slate-300 transition-smooth space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-mono font-bold text-slate-400">
                              Ch {ch.number}
                            </span>
                            <span className={`text-[10px] px-2.5 py-0.5 rounded-full ${badgeColor}`}>
                              {ch.priority}
                            </span>
                            {ch.upscRelevance && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-600 border border-slate-200 font-medium">
                                {ch.upscRelevance} Relevance
                              </span>
                            )}
                          </div>
                          <h4 className="font-display font-bold text-sm sm:text-base text-slate-900">
                            {ch.title}
                          </h4>
                        </div>

                        {/* Resource State Actions */}
                        <div className="flex items-center gap-2 shrink-0">
                          {hasResource ? (
                            <Link
                              href={`/study?subject=${encodeURIComponent(activeBook.subjectName)}&topic=${encodeURIComponent(`Ch ${ch.number}: ${ch.title}`)}&duration=25`}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-[11px] font-semibold transition-smooth shadow-subtle"
                            >
                              <Play className="w-3 h-3 fill-current" />
                              <span>Study Chapter</span>
                            </Link>
                          ) : (
                            <div className="flex items-center gap-2">
                              <span className="text-[11px] text-slate-400 font-sans">
                                Resources unavailable
                              </span>
                              <button
                                type="button"
                                onClick={() => setSuggestModalChapter({ chapterNum: ch.number, title: ch.title, subject: activeBook.subjectName })}
                                className="px-2.5 py-1 rounded-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-[10px] font-semibold transition-smooth"
                              >
                                Suggest Resource
                              </button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* UPSC Relevance Note */}
                      <p className="text-xs text-slate-600 font-sans leading-relaxed">
                        <strong className="text-slate-900 font-semibold">UPSC Signal: </strong>
                        {ch.upscRelevanceNote}
                      </p>

                      {/* Key Themes Pill Tag List */}
                      {ch.keyThemes && ch.keyThemes.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap pt-1">
                          {ch.keyThemes.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-0.5 rounded-full bg-white text-slate-600 text-[10px] font-sans border border-slate-200/60"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Revision & Next Step */}
            <div className="pt-4 border-t border-slate-150 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-slate-500 font-sans">
              <div>
                <strong className="text-slate-900 font-semibold">Next recommended step: </strong>
                <span>{activeBook.nextStep}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>Mark completed:</span>
                <input
                  type="checkbox"
                  checked={(userProgress[activeBook.id] || 0) === 100}
                  onChange={(e) => handleProgressUpdate(activeBook.id, e.target.checked ? 100 : 0)}
                  className="w-4 h-4 rounded text-slate-900 focus:ring-slate-900 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Suggest / Report Resource Modal */}
      {suggestModalChapter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 sm:p-7 shadow-2xl border border-slate-200 space-y-4 relative">
            <h3 className="font-display font-bold text-base text-slate-900">
              Suggest Resource for Chapter {suggestModalChapter.chapterNum > 0 ? suggestModalChapter.chapterNum : ''}
            </h3>
            <p className="text-xs text-slate-500 font-sans">
              {suggestModalChapter.subject} — {suggestModalChapter.title}
            </p>

            {suggestSuccess ? (
              <div className="p-4 rounded-xl bg-emerald-50 text-emerald-800 text-xs space-y-2 text-center">
                <p className="font-semibold">Thank you for helping verify UPSC resources!</p>
                <p className="text-[11px] text-emerald-700">Our academic team will review and index this resource.</p>
                <button
                  type="button"
                  onClick={() => { setSuggestModalChapter(null); setSuggestSuccess(false); }}
                  className="mt-2 px-4 py-2 rounded-full bg-slate-900 text-white text-xs font-semibold"
                >
                  Close
                </button>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setSuggestSuccess(true);
                }}
                className="space-y-3 text-xs"
              >
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">YouTube URL or Notes Link</label>
                  <input
                    type="url"
                    required
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="w-full p-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Educator / Channel Name</label>
                  <input
                    type="text"
                    placeholder="e.g. PW OnlyIAS, StudyIQ, Unacademy"
                    className="w-full p-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSuggestModalChapter(null)}
                    className="px-4 py-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold"
                  >
                    Submit Resource
                  </button>
                </div>
              </form>
            )}
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

export default function NCERTFoundationPage() {
  return (
    <Suspense fallback={
      <div className="w-full max-w-[1500px] mx-auto px-4 py-32 text-center space-y-2">
        <div className="w-6 h-6 rounded-full border-2 border-slate-900 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-slate-400 font-medium">Loading NCERT Foundation Curriculum...</p>
      </div>
    }>
      <NCERTFoundationContent />
    </Suspense>
  );
}
