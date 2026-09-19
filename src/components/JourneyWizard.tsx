'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowRight, 
  CheckCircle2, 
  RotateCcw,
  Sparkles,
  BookOpen,
  Calendar
} from 'lucide-react';
import { UserGeneratedPlan } from '../lib/types';
import { saveLocalProgress } from '../lib/store';
import SeniorGuidanceBox from './SeniorGuidanceBox';

export default function JourneyWizard() {
  const [step, setStep] = useState<number>(1);
  const [currentLevel, setCurrentLevel] = useState<string>('Beginner UPSC aspirant');
  const [dailyHours, setDailyHours] = useState<string>('3–4 hours/day');
  const [targetGoal, setTargetGoal] = useState<string>('UPSC 2027');
  const [generatedPlan, setGeneratedPlan] = useState<UserGeneratedPlan | null>(null);

  const levelOptions = [
    { id: 'Class 6–10 foundation', title: 'School Foundation (Class 6–10)', desc: 'Zero background, wants to build strong basic roots' },
    { id: 'Class 11–12', title: 'Class 11–12 Senior Secondary', desc: 'Cover Humanities & Science NCERTs alongside school exams' },
    { id: 'College student', title: 'College Student (Graduation)', desc: 'Balanced 2–3 daily hours alongside a university degree' },
    { id: 'Beginner UPSC aspirant', title: 'Zero Beginner (Starting Fresh)', desc: 'Direct guidance from Class 6 NCERTs through standard reference texts' },
    { id: 'Already preparing', title: 'Intermediate Aspirant', desc: 'Finished basic NCERTs, now targeting Standard Books & PYQs' },
  ];

  const timeOptions = [
    { id: '1 hour/day', title: '1 hour / day', desc: 'Minimalist habit building for working professionals' },
    { id: '2 hours/day', title: '2 hours / day', desc: 'Steady foundation pace (1 chapter + 20 min editorial summary)' },
    { id: '3–4 hours/day', title: '3–4 hours / day', desc: 'Recommended balanced pace for standard UPSC preparation' },
    { id: '5+ hours/day', title: '5+ hours / day', desc: 'Dedicated full-time mode (NCERTs + Standard texts + PYQs)' },
  ];

  const goalOptions = [
    { id: 'Build foundation', title: 'Pure Foundation', desc: 'Complete Class 6–12 NCERTs with rock-solid conceptual clarity' },
    { id: 'UPSC 2027', title: 'Target UPSC CSE 2027', desc: 'Structured 18-month roadmap: Foundation → Standard → Practice' },
    { id: 'UPSC 2028', title: 'Target UPSC CSE 2028', desc: 'Long-term 2-3 year academic plan (Ideal for early college students)' },
    { id: 'Prelims', title: 'Prelims Stage Focus', desc: 'High-yield static core, CSAT practice, and MCQs' },
  ];

  const generateRoadmap = () => {
    const weeks = [
      {
        weekNumber: 1,
        title: 'Phase 1: History & Geography NCERT Kickoff',
        focusSubjects: ['History Class 6', 'Geography Class 6', 'Daily Newspaper Habit'],
        targets: [
          'Read Class 6 Our Pasts - I (Harappa, Vedic age, Ashoka edicts)',
          'Read Class 6 The Earth Our Habitat (Latitudes, Longitudes, Solstice diagram)',
          'Establish 20-minute daily habit with The Hindu or Indian Express Explained'
        ],
        estimatedHoursPerWeek: dailyHours.includes('1') ? 7 : dailyHours.includes('2') ? 14 : 24,
        seniorTip: 'Don’t try to memorize dates in Week 1. Just get comfortable with reading 15 pages a day.'
      },
      {
        weekNumber: 2,
        title: 'Phase 1: Class 7 Medieval & Environmental Systems',
        focusSubjects: ['History Class 7', 'Geography Class 7', 'Civics Class 6–7'],
        targets: [
          'Read Class 7 Our Pasts - II (Chola local autonomy, Delhi Sultanate, Mughals)',
          'Read Class 7 Our Environment (5 Layers of Atmosphere & Ocean Currents)',
          'Read Class 6–7 Civics (Panchayati Raj 3-tier structure & State Government)'
        ],
        estimatedHoursPerWeek: dailyHours.includes('1') ? 7 : dailyHours.includes('2') ? 14 : 24,
        seniorTip: 'Medieval terms like Mansabdari and Iqta are frequently asked. Note them down in your personal notebook.'
      },
      {
        weekNumber: 3,
        title: 'Phase 2: Class 8 Modern India & Indian Constitution Bedrock',
        focusSubjects: ['History Class 8', 'Civics Class 8', 'Mapping'],
        targets: [
          'Read Class 8 Our Pasts - III (Zamindari vs Ryotwari vs Mahalwari systems)',
          'Read Class 8 Civics (Indian Secularism vs Western Secularism & Judiciary)',
          'Practice drawing India physical relief boundaries & major river flows'
        ],
        estimatedHoursPerWeek: dailyHours.includes('1') ? 7 : dailyHours.includes('2') ? 14 : 24,
        seniorTip: 'Ye topic pehle clear kar lo, because later Laxmikanth and Spectrum will assume you already know this.'
      },
      {
        weekNumber: 4,
        title: 'Phase 2: Class 9–10 Economy & Indian Drainage Mastery',
        focusSubjects: ['Economics Class 9–10', 'Geography Class 9 (Monsoon & Rivers)'],
        targets: [
          'Understand 4 Factors of Production, Disguised Unemployment, MSP and PDS in Class 9 Economics',
          'Study Class 9 Drainage (Indus, Ganga, Brahmaputra, Godavari tributaries)',
          'Understand Indian Monsoon mechanism (ITCZ, Jet Streams, El Niño basics)'
        ],
        estimatedHoursPerWeek: dailyHours.includes('1') ? 7 : dailyHours.includes('2') ? 14 : 24,
        seniorTip: 'Economics Class 9 and 10 will give you the confidence that economy is not just about math—it is about real life in India.'
      },
      {
        weekNumber: 5,
        title: 'Phase 3: The Golden Milestone (Class 11 Constitution at Work)',
        focusSubjects: ['Polity Class 11', 'PYQ Orientation'],
        targets: [
          'Read all 10 chapters of "Indian Constitution at Work" (Fundamental Rights, Writs, Parliament, Federalism)',
          'Compare First Past the Post (FPTP) vs Proportional Representation (PR)',
          'Solve 25 past Prelims questions on Fundamental Rights to check retention'
        ],
        estimatedHoursPerWeek: dailyHours.includes('1') ? 7 : dailyHours.includes('2') ? 14 : 24,
        seniorTip: 'This is the most critical book in the entire NCERT journey. Read it slowly and make your own margin notes.'
      },
      {
        weekNumber: 6,
        title: 'Phase 3: Class 11 Physical Geography & Indian Economic Development',
        focusSubjects: ['Geography Class 11', 'Economics Class 11 (1991 LPG Reforms)'],
        targets: [
          'Study Plate Tectonics, Pressure Belts, and Cyclones in Fundamentals of Physical Geography',
          'Read Indian Economic Development (Pre-1991 stagnation, 1991 LPG crisis, and Rural credit)',
          'Start weekly CSAT practice (1 hour of Number System & Reading Comprehension)'
        ],
        estimatedHoursPerWeek: dailyHours.includes('1') ? 7 : dailyHours.includes('2') ? 14 : 24,
        seniorTip: 'After completing Week 6, you will be ahead of 80% of serious aspirants in conceptual clarity. Move to Laxmikanth & Spectrum next.'
      }
    ];

    const plan: UserGeneratedPlan = {
      currentLevel,
      dailyHours,
      targetGoal,
      generatedDate: new Date().toISOString(),
      weeklySchedule: weeks
    };

    setGeneratedPlan(plan);
    saveLocalProgress({ activePlan: plan });
    setStep(4);
  };

  return (
    <div className="pt-24 sm:pt-32 pb-24 max-w-4xl mx-auto px-4 sm:px-6 space-y-12">
      {/* Header */}
      <div className="space-y-2 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700">
          <span>STUDY NAVIGATOR</span>
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl text-slate-900 tracking-tight">
          Personalize your journey.
        </h1>
        <p className="text-sm sm:text-base text-slate-500 font-sans">
          Answer 3 simple questions to generate a balanced weekly sequence without timetable anxiety.
        </p>
      </div>

      {/* Segmented Step Indicator */}
      <div className="flex items-center justify-center gap-2">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              step === i
                ? 'w-10 bg-slate-900'
                : step > i
                ? 'w-6 bg-slate-300'
                : 'w-6 bg-slate-200'
            }`}
          />
        ))}
      </div>

      {/* Step 1: Starting Level */}
      {step === 1 && (
        <div className="p-8 sm:p-10 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Step 01</span>
            <h3 className="font-display font-bold text-xl text-slate-900">Where are you starting from?</h3>
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {levelOptions.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setCurrentLevel(opt.id)}
                className={`p-4 rounded-2xl text-left border transition-smooth flex items-center justify-between ${
                  currentLevel === opt.id
                    ? 'border-slate-900 bg-slate-900 text-white shadow-subtle'
                    : 'border-slate-200/80 bg-slate-50/50 hover:bg-slate-100/70 text-slate-800'
                }`}
              >
                <div>
                  <div className="font-display font-bold text-sm">{opt.title}</div>
                  <p className={`text-xs mt-0.5 font-sans ${currentLevel === opt.id ? 'text-slate-300' : 'text-slate-500'}`}>
                    {opt.desc}
                  </p>
                </div>
                {currentLevel === opt.id && <CheckCircle2 className="w-4 h-4 text-white" />}
              </button>
            ))}
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-subtle transition-smooth"
            >
              <span>Next: Available Hours</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Available Daily Time */}
      {step === 2 && (
        <div className="p-8 sm:p-10 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Step 02</span>
            <h3 className="font-display font-bold text-xl text-slate-900">How many daily hours can you commit?</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {timeOptions.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setDailyHours(opt.id)}
                className={`p-5 rounded-2xl text-left border transition-smooth flex flex-col justify-between ${
                  dailyHours === opt.id
                    ? 'border-slate-900 bg-slate-900 text-white shadow-subtle'
                    : 'border-slate-200/80 bg-slate-50/50 hover:bg-slate-100/70 text-slate-800'
                }`}
              >
                <div className="font-display font-bold text-base">{opt.title}</div>
                <p className={`text-xs mt-2 font-sans ${dailyHours === opt.id ? 'text-slate-300' : 'text-slate-500'}`}>
                  {opt.desc}
                </p>
              </button>
            ))}
          </div>

          <div className="flex justify-between items-center pt-2">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="text-xs font-medium text-slate-500 hover:text-slate-900"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={() => setStep(3)}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-subtle transition-smooth"
            >
              <span>Next: Target Goal</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Target Goal */}
      {step === 3 && (
        <div className="p-8 sm:p-10 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Step 03</span>
            <h3 className="font-display font-bold text-xl text-slate-900">What is your primary preparation goal?</h3>
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {goalOptions.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setTargetGoal(opt.id)}
                className={`p-4 rounded-2xl text-left border transition-smooth flex items-center justify-between ${
                  targetGoal === opt.id
                    ? 'border-slate-900 bg-slate-900 text-white shadow-subtle'
                    : 'border-slate-200/80 bg-slate-50/50 hover:bg-slate-100/70 text-slate-800'
                }`}
              >
                <div>
                  <div className="font-display font-bold text-sm">{opt.title}</div>
                  <p className={`text-xs mt-0.5 font-sans ${targetGoal === opt.id ? 'text-slate-300' : 'text-slate-500'}`}>
                    {opt.desc}
                  </p>
                </div>
                {targetGoal === opt.id && <CheckCircle2 className="w-4 h-4 text-white" />}
              </button>
            ))}
          </div>

          <div className="flex justify-between items-center pt-2">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="text-xs font-medium text-slate-500 hover:text-slate-900"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={generateRoadmap}
              className="inline-flex items-center gap-2 px-7 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-subtle transition-smooth"
            >
              <span>Generate My Roadmap</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Generated Output */}
      {step === 4 && generatedPlan && (
        <div className="space-y-8">
          {/* Summary */}
          <div className="p-8 sm:p-10 rounded-4xl bg-slate-900 text-white space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Personalized Learning Sequence
              </span>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Recalculate</span>
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 text-xs font-sans">
              <div>
                <span className="text-slate-400 block mb-0.5">Level</span>
                <span className="font-semibold text-white">{generatedPlan.currentLevel}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Budget</span>
                <span className="font-semibold text-white">{generatedPlan.dailyHours}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Target</span>
                <span className="font-semibold text-white">{generatedPlan.targetGoal}</span>
              </div>
            </div>
          </div>

          <SeniorGuidanceBox
            title="Senior Mentor Orientation"
            advice="Follow Week 1 targets without rushing. NCERT foundation clear hone ke baad standard reference books 3x speed se samajh aati hain."
          />

          {/* Weekly Schedule Stack */}
          <div className="space-y-4">
            <h3 className="font-display font-bold text-lg text-slate-900">
              Week-by-Week Action Sequence
            </h3>

            <div className="space-y-3">
              {generatedPlan.weeklySchedule.map((w) => (
                <div
                  key={w.weekNumber}
                  className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-subtle space-y-3"
                >
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                    <span className="font-mono text-xs font-bold text-slate-400">
                      WEEK 0{w.weekNumber}
                    </span>
                    <span className="text-[11px] text-slate-400 font-medium">
                      ~{w.estimatedHoursPerWeek}h total
                    </span>
                  </div>

                  <h4 className="font-display font-bold text-base text-slate-900">{w.title}</h4>

                  <ul className="space-y-1.5 pt-1">
                    {w.targets.map((t, idx) => (
                      <li key={idx} className="text-xs text-slate-600 font-sans flex items-start gap-2">
                        <span className="text-slate-400 mt-0.5">•</span>
                        <span>{t}</span>
                      </li>
                    ))}
                  </ul>

                  <p className="text-xs text-slate-500 font-sans italic pt-1">
                    “{w.seniorTip}”
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Action Footer */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200/80 flex items-center justify-between">
            <span className="text-xs font-medium text-slate-600">Saved to your Personal Dashboard</span>
            <Link
              href="/ncert?class=6"
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-slate-900 text-white font-medium text-xs"
            >
              <span>Begin Week 1 (Class 6 NCERT)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
