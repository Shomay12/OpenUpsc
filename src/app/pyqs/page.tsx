'use client';

import React, { useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { 
  CheckSquare, 
  ArrowUpRight, 
  Eye, 
  Edit3, 
  RotateCcw,
  CheckCircle2
} from 'lucide-react';
import { PYQ_ITEMS } from '../../data/pyqData';
import { PYQItem } from '../../lib/types';
import SeniorGuidanceBox from '../../components/SeniorGuidanceBox';
import NotesModal from '../../components/NotesModal';

function PYQVaultContent() {
  const searchParams = useSearchParams();
  const initialType = searchParams.get('type') || 'All';

  const [selectedType, setSelectedType] = useState<string>(initialType);
  const [selectedSubject, setSelectedSubject] = useState<string>('All');
  const [selectedYear, setSelectedYear] = useState<string>('All');
  const [revealedAnswers, setRevealedAnswers] = useState<Record<string, boolean>>({});
  const [selectedUserAnswers, setSelectedUserAnswers] = useState<Record<string, string>>({});
  const [notesModalData, setNotesModalData] = useState<{ id: string; title: string; category: string } | null>(null);

  const toggleReveal = (id: string) => {
    setRevealedAnswers(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSelectOption = (pyqId: string, opt: string) => {
    setSelectedUserAnswers(prev => ({ ...prev, [pyqId]: opt }));
    setRevealedAnswers(prev => ({ ...prev, [pyqId]: true }));
  };

  const filteredPYQs = PYQ_ITEMS.filter((item) => {
    if (selectedType !== 'All' && item.type !== selectedType) return false;
    if (selectedSubject !== 'All' && item.subject !== selectedSubject) return false;
    if (selectedYear !== 'All' && String(item.year) !== selectedYear) return false;
    return true;
  });

  const subjects = ['All', 'Indian Polity', 'History', 'Geography', 'Economy'];

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700">
          <span>EXAM ARCHIVES</span>
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
          Previous Year Questions
        </h1>
        <p className="text-sm sm:text-base text-slate-500 font-sans max-w-2xl leading-relaxed">
          Authentic UPSC Prelims & Mains examination questions with elimination strategies and direct roadmap connections.
        </p>
      </div>

      <SeniorGuidanceBox
        title="Senior Elimination Method"
        advice="Analyze wrong options in PYQs. In 2021, UPSC turned wrong choices from the 2018 exam into active questions. Treat every option as a learning syllabus item."
      />

      {/* Filter Row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 sm:p-5 rounded-2xl bg-white border border-slate-200/80 shadow-subtle">
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none no-scrollbar w-full sm:w-auto pb-1 sm:pb-0">
          {/* Stage toggle */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-full text-xs font-semibold flex-shrink-0">
            {['All', 'Prelims', 'Mains'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-3 py-1 rounded-full transition-smooth ${
                  selectedType === t ? 'bg-white text-slate-900 shadow-subtle' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Subject Pills */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {subjects.map((s) => (
              <button
                key={s}
                onClick={() => setSelectedSubject(s)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth flex-shrink-0 ${
                  selectedSubject === s
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <span className="text-xs text-slate-400 font-medium shrink-0">
          {filteredPYQs.length} questions
        </span>
      </div>

      {/* Questions Stack */}
      <div className="space-y-6">
        {filteredPYQs.map((pyq, index) => {
          const isRevealed = revealedAnswers[pyq.id];
          const userSelected = selectedUserAnswers[pyq.id];

          return (
            <div
              key={pyq.id}
              className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-6"
            >
              {/* Top metadata */}
              <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <span className="font-mono text-slate-400 font-bold">0{index + 1}</span>
                  <span className="font-semibold text-slate-900">{pyq.type} {pyq.year}</span>
                  <span className="text-slate-300">·</span>
                  <span className="text-slate-500">{pyq.subject}</span>
                  <span className="text-slate-300">·</span>
                  <span className="text-slate-500">{pyq.topic}</span>
                </div>

                <button
                  type="button"
                  onClick={() => setNotesModalData({ id: pyq.id, title: `${pyq.subject} PYQ (${pyq.year})`, category: 'PYQ Note' })}
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-900"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Note</span>
                </button>
              </div>

              {/* Question Text */}
              <div className="space-y-4">
                <p className="font-sans text-sm sm:text-base text-slate-900 leading-relaxed font-normal whitespace-pre-line">
                  {pyq.question}
                </p>

                {/* Multiple Choice Options */}
                {pyq.options && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {pyq.options.map((opt, optIdx) => {
                      const isOptionCorrect = isRevealed && opt === pyq.correctAnswer;
                      const isOptionWrongSelected = isRevealed && userSelected === opt && opt !== pyq.correctAnswer;
                      const isOptionChosen = userSelected === opt;

                      return (
                        <button
                          key={optIdx}
                          type="button"
                          onClick={() => handleSelectOption(pyq.id, opt)}
                          className={`p-3.5 rounded-xl border text-left text-xs font-sans transition-smooth flex items-start gap-3 ${
                            isOptionCorrect
                              ? 'bg-emerald-50/50 border-emerald-300 text-emerald-950 font-semibold'
                              : isOptionWrongSelected
                              ? 'bg-rose-50/40 border-rose-200 text-rose-900 line-through'
                              : isOptionChosen
                              ? 'bg-slate-100 border-slate-300 text-slate-900'
                              : 'bg-slate-50/60 border-slate-200/80 hover:bg-slate-100 text-slate-700'
                          }`}
                        >
                          <span className="font-mono font-bold text-slate-400 text-[11px] mt-0.5">
                            {String.fromCharCode(65 + optIdx)}
                          </span>
                          <span>{opt}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Actions & Reveal */}
              <div className="pt-2 flex items-center justify-between gap-4">
                <button
                  type="button"
                  onClick={() => toggleReveal(pyq.id)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors"
                >
                  <Eye className="w-3.5 h-3.5 text-slate-600" />
                  <span>{isRevealed ? 'Hide Explanation' : 'Show Explanation'}</span>
                </button>

                {pyq.relatedSubjectPath && (
                  <Link
                    href={pyq.relatedSubjectPath}
                    className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
                  >
                    <span>Related Pathway</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>

              {/* Explanation Box */}
              {isRevealed && (
                <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3 text-xs animate-in fade-in duration-150">
                  {pyq.correctAnswer && (
                    <span className="inline-block font-semibold text-emerald-800 bg-emerald-100/60 px-2.5 py-0.5 rounded-full">
                      Correct: {pyq.correctAnswer}
                    </span>
                  )}

                  <p className="text-slate-700 leading-relaxed font-sans whitespace-pre-line">
                    {pyq.explanation}
                  </p>

                  <div className="p-3.5 rounded-xl bg-white border border-slate-200/60 text-slate-600 font-sans">
                    <strong className="text-slate-900 block text-[11px] mb-0.5">Senior Elimination Tip:</strong>
                    “{pyq.seniorApproachTip}”
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {notesModalData && (
        <NotesModal
          isOpen={!!notesModalData}
          onClose={() => setNotesModalData(null)}
          itemId={notesModalData.id}
          itemTitle={notesModalData.title}
          itemCategory={notesModalData.category}
        />
      )}
    </div>
  );
}

export default function PYQVaultPage() {
  return (
    <Suspense fallback={
      <div className="w-full max-w-[1500px] mx-auto px-4 py-32 text-center space-y-2">
        <div className="w-6 h-6 rounded-full border-2 border-slate-900 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-slate-400 font-medium">Loading Questions Vault...</p>
      </div>
    }>
      <PYQVaultContent />
    </Suspense>
  );
}
