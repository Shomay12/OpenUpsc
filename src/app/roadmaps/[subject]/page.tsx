'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  Clock, 
  Edit3, 
  ExternalLink, 
  Target, 
  ArrowUpRight 
} from 'lucide-react';
import { SUBJECT_ROADMAPS } from '../../../data/subjectRoadmaps';
import SeniorGuidanceBox from '../../../components/SeniorGuidanceBox';
import ResourceCard from '../../../components/ResourceCard';
import ProgressBadge from '../../../components/ProgressBadge';
import NotesModal from '../../../components/NotesModal';
import { getLocalProgress, saveLocalProgress } from '../../../lib/store';

export default function SubjectRoadmapDetailPage() {
  const params = useParams();
  const subjectId = params.subject as string;

  const roadmap = SUBJECT_ROADMAPS.find((r) => r.subjectId === subjectId);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [userProgress, setUserProgress] = useState<Record<string, number>>({});
  const [notesModalData, setNotesModalData] = useState<{ id: string; title: string; category: string } | null>(null);

  useEffect(() => {
    const stored = getLocalProgress();
    setUserProgress(stored.progressPercentMap || {});
  }, []);

  if (!roadmap) {
    return (
      <div className="w-full max-w-[1500px] mx-auto py-24 text-center space-y-4">
        <h2 className="font-display font-bold text-2xl text-slate-900">Roadmap Not Found</h2>
        <Link href="/roadmaps" className="text-xs font-semibold text-slate-900 underline">
          ← Back to All Roadmaps
        </Link>
      </div>
    );
  }

  const activeStep = roadmap.steps[activeStepIndex] || roadmap.steps[0];

  const handleProgressUpdate = (id: string, percent: number) => {
    const updated = { ...userProgress, [id]: percent };
    setUserProgress(updated);
    saveLocalProgress({ progressPercentMap: updated });
  };

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      <div>
        <Link
          href="/roadmaps"
          className="inline-flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Roadmaps</span>
        </Link>
      </div>

      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700">
          <span>SUBJECT PROGRESSION</span>
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
          {roadmap.subjectName}
        </h1>
        <p className="text-sm sm:text-base text-slate-500 font-sans max-w-2xl leading-relaxed">
          {roadmap.description}
        </p>
      </div>

      <SeniorGuidanceBox
        advice={roadmap.overviewAdvice}
        title={`${roadmap.subjectName} Strategy`}
      />

      {/* Step Progression Segmented Nodes */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 text-xs">
          <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
            Milestones Sequence
          </span>
          <span className="font-medium text-slate-500">
            Step {activeStepIndex + 1} of {roadmap.steps.length}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {roadmap.steps.map((st, idx) => {
            const isSelected = activeStepIndex === idx;
            const pct = userProgress[st.id] || 0;
            return (
              <button
                key={st.id}
                type="button"
                onClick={() => setActiveStepIndex(idx)}
                className={`p-3 rounded-xl text-left transition-smooth flex flex-col justify-between ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-subtle'
                    : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`font-mono text-[10px] font-bold ${isSelected ? 'text-slate-400' : 'text-slate-400'}`}>
                    0{idx + 1}
                  </span>
                  {pct === 100 && (
                    <span className="text-[10px] text-emerald-400 font-bold">✓</span>
                  )}
                </div>
                <h4 className="font-display font-bold text-xs line-clamp-1">
                  {st.title.split('(')[0]}
                </h4>
                <span className={`text-[10px] mt-1 ${isSelected ? 'text-slate-300' : 'text-slate-400'}`}>
                  {st.level}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Step Container */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-8">
        {/* Step Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Step 0{activeStep.stepNumber} · {activeStep.level}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                ~{activeStep.estimatedTime}
              </span>
            </div>
            <h2 className="font-display font-bold text-2xl sm:text-3xl text-slate-900 tracking-tight">
              {activeStep.title}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 font-sans">
              {activeStep.tagline}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="space-y-0.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                Milestone Status
              </span>
              <ProgressBadge
                itemId={activeStep.id}
                currentPercent={userProgress[activeStep.id] || 0}
                onUpdate={(pct) => handleProgressUpdate(activeStep.id, pct)}
              />
            </div>

            <button
              type="button"
              onClick={() => setNotesModalData({ id: activeStep.id, title: activeStep.title, category: `${roadmap.subjectName} Step ${activeStep.stepNumber}` })}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors mt-auto"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Notes</span>
            </button>
          </div>
        </div>

        {/* Step Mentor Note */}
        <div className="p-5 rounded-xl bg-slate-50 border border-slate-150 text-xs sm:text-sm text-slate-700 font-sans leading-relaxed">
          <span className="font-semibold text-slate-900 uppercase tracking-wider text-[10px] block mb-1">
            Mentor Step Focus
          </span>
          “{activeStep.seniorGuidance}”
        </div>

        {/* Action Checklist & PYQ Focus Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-6 rounded-2xl bg-slate-50/80 border border-slate-150 space-y-3">
            <h3 className="font-display font-bold text-slate-900 text-sm flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-slate-900" />
              <span>Concrete Milestone Checklist</span>
            </h3>
            <ul className="space-y-2">
              {activeStep.actionChecklist.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-600 font-sans">
                  <span className="w-4 h-4 rounded-full bg-white border border-slate-200 text-slate-700 flex items-center justify-center font-mono text-[10px] font-bold flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50/80 border border-slate-150 space-y-3">
            <h3 className="font-display font-bold text-slate-900 text-sm flex items-center gap-2">
              <Target className="w-4 h-4 text-slate-900" />
              <span>PYQ Relevance & Pattern</span>
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed font-sans">
              {activeStep.pyqFocusArea}
            </p>
            <div className="pt-2">
              <Link
                href="/pyqs"
                className="inline-flex items-center gap-1 text-xs font-semibold text-slate-900 hover:text-slate-600"
              >
                <span>Practice Relevant Questions</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Embedded Resource Cards */}
        {activeStep.resources && activeStep.resources.length > 0 && (
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <h3 className="font-display font-bold text-slate-900 text-base">
              Recommended Free Resources for this Step
            </h3>

            <div className="grid grid-cols-1 gap-4">
              {activeStep.resources.map((res) => (
                <ResourceCard
                  key={res.id}
                  resource={res}
                  userProgressPercent={userProgress[res.id] || 0}
                  onProgressUpdate={handleProgressUpdate}
                />
              ))}
            </div>
          </div>
        )}

        {/* Step Navigation Controls */}
        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
          <button
            type="button"
            disabled={activeStepIndex === 0}
            onClick={() => setActiveStepIndex((prev) => Math.max(0, prev - 1))}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-full border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous Step</span>
          </button>

          {activeStepIndex < roadmap.steps.length - 1 ? (
            <button
              type="button"
              onClick={() => setActiveStepIndex((prev) => Math.min(roadmap.steps.length - 1, prev + 1))}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-subtle transition-smooth"
            >
              <span>Next Step: {roadmap.steps[activeStepIndex + 1]?.title.split('(')[0]}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <Link
              href="/roadmaps"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-slate-900 text-white font-medium text-xs shadow-subtle transition-smooth"
            >
              <span>Pathway Completed! View All Roadmaps</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>
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
