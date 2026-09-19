'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowRight, 
  Check, 
  Sparkles, 
  Compass, 
  Target, 
  Clock, 
  BookOpen 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function OnboardingPage() {
  const router = useRouter();
  const { profile, updateProfile, refreshProfile } = useAuth();
  
  const [step, setStep] = useState<number>(1);
  const [stage, setStage] = useState<string>('School / Foundation');
  const [targetYear, setTargetYear] = useState<string>('2028');
  const [targetHours, setTargetHours] = useState<number>(4);
  const [saving, setSaving] = useState<boolean>(false);

  const stages = [
    { id: 'School / Foundation', title: 'School / Foundation', desc: 'Starting from foundational concepts and Class 6–12 NCERTs' },
    { id: 'College', title: 'College', desc: 'Building conceptual depth alongside university studies' },
    { id: 'Beginner UPSC aspirant', title: 'Beginner UPSC aspirant', desc: 'Dedicated full-time aspirant stepping into standard core' },
    { id: 'Already preparing', title: 'Already preparing', desc: 'Covered standard syllabus; focusing on practice, revision, and PYQs' },
  ];

  const targetYears = ['2027', '2028', '2029', 'Not decided'];
  const dailyHourOptions = [
    { value: 1, label: '1 hour' },
    { value: 2, label: '2 hours' },
    { value: 3, label: '3 hours' },
    { value: 4, label: '4 hours' },
    { value: 5, label: '5+ hours' },
  ];

  const handleFinish = async () => {
    setSaving(true);
    try {
      await updateProfile({
        preparationStage: stage,
        targetAttemptYear: targetYear,
        dailyTargetHours: targetHours,
      });
      await refreshProfile();
      router.push('/dashboard');
    } catch (e) {
      console.error(e);
      router.push('/dashboard');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pt-24 sm:pt-32 pb-24 max-w-xl mx-auto px-4 sm:px-6 space-y-8">
      {/* Progress step dots */}
      <div className="flex items-center justify-center gap-2">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              step === s
                ? 'w-8 bg-slate-900'
                : step > s
                ? 'w-4 bg-emerald-500'
                : 'w-4 bg-slate-200'
            }`}
          />
        ))}
      </div>

      <div className="p-6 sm:p-10 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-8 animate-in fade-in duration-200">
        {/* STEP 1: PREPARATION STAGE */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <Compass className="w-4 h-4 text-slate-700" />
                <span>Step 1 of 3</span>
              </div>
              <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900">
                What’s your preparation stage?
              </h2>
              <p className="text-xs text-slate-500 font-sans">
                This personalizes your default roadmap milestones and daily focus recommendations.
              </p>
            </div>

            <div className="space-y-2.5">
              {stages.map((st) => {
                const isSelected = stage === st.id;
                return (
                  <button
                    key={st.id}
                    type="button"
                    onClick={() => setStage(st.id)}
                    className={`w-full p-4 rounded-3xl text-left border transition-smooth flex items-center justify-between gap-4 ${
                      isSelected
                        ? 'bg-slate-900 text-white border-slate-900 shadow-subtle'
                        : 'bg-slate-50/70 hover:bg-slate-100 text-slate-800 border-slate-200/70'
                    }`}
                  >
                    <div>
                      <h4 className={`text-xs sm:text-sm font-semibold ${isSelected ? 'text-white' : 'text-slate-900'}`}>
                        {st.title}
                      </h4>
                      <p className={`text-[11px] ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                        {st.desc}
                      </p>
                    </div>
                    {isSelected && (
                      <div className="w-6 h-6 rounded-full bg-white text-slate-900 flex items-center justify-center text-xs font-bold shrink-0">
                        ✓
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => router.push('/dashboard')}
                className="text-xs text-slate-400 hover:text-slate-700 font-medium"
              >
                Skip for now
              </button>
              <button
                type="button"
                onClick={() => setStep(2)}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
              >
                <span>Continue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: TARGET ATTEMPT YEAR */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <Target className="w-4 h-4 text-slate-700" />
                <span>Step 2 of 3</span>
              </div>
              <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900">
                When is your target attempt?
              </h2>
              <p className="text-xs text-slate-500 font-sans">
                Set a long-term horizon for your learning timeline.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {targetYears.map((yr) => {
                const isSelected = targetYear === yr;
                return (
                  <button
                    key={yr}
                    type="button"
                    onClick={() => setTargetYear(yr)}
                    className={`p-4 rounded-3xl text-center border font-display font-bold text-sm sm:text-base transition-smooth ${
                      isSelected
                        ? 'bg-slate-900 text-white border-slate-900 shadow-subtle'
                        : 'bg-slate-50 hover:bg-slate-100 text-slate-800 border-slate-200'
                    }`}
                  >
                    {yr}
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs text-slate-500 hover:text-slate-800 font-medium"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
              >
                <span>Continue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: DAILY STUDY TARGET */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <Clock className="w-4 h-4 text-slate-700" />
                <span>Step 3 of 3</span>
              </div>
              <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900">
                Daily study target
              </h2>
              <p className="text-xs text-slate-500 font-sans">
                Set a realistic daily focused hours goal. Consistency beats sporadic bursts.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {dailyHourOptions.map((opt) => {
                const isSelected = targetHours === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setTargetHours(opt.value)}
                    className={`py-3.5 px-4 rounded-2xl text-center border font-display font-bold text-xs sm:text-sm transition-smooth ${
                      isSelected
                        ? 'bg-slate-900 text-white border-slate-900 shadow-subtle'
                        : 'bg-slate-50 hover:bg-slate-100 text-slate-800 border-slate-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="text-xs text-slate-500 hover:text-slate-800 font-medium"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleFinish}
                disabled={saving}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
              >
                <span>{saving ? 'Saving...' : 'Enter Workspace'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
