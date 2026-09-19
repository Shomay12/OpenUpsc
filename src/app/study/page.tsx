'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle2, 
  Clock, 
  Maximize2, 
  Minimize2, 
  ArrowRight, 
  Calendar, 
  History, 
  BookOpen, 
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { StudySession, TimetableEvent } from '../../lib/types';
import { getLocalProgress, addStudySession, saveLocalProgress } from '../../lib/store';
import SeniorGuidanceBox from '../../components/SeniorGuidanceBox';

function StudyTimerContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialSubject = searchParams.get('subject') || 'History';
  const initialTopic = searchParams.get('topic') || 'Modern Indian History (Revolt of 1857)';
  const initialMinutes = Number(searchParams.get('duration')) || 25;
  const initialResourceId = searchParams.get('resourceId') || '';

  const [mode, setMode] = useState<'Focus' | 'Short Break' | 'Long Break'>('Focus');
  const [targetDurationMinutes, setTargetDurationMinutes] = useState<number>(initialMinutes);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(initialMinutes * 60);
  const [isActive, setIsActive] = useState<boolean>(false);
  const [isDistractionFree, setIsDistractionFree] = useState<boolean>(false);
  const [selectedSubject, setSelectedSubject] = useState<string>(initialSubject);
  const [selectedTopic, setSelectedTopic] = useState<string>(initialTopic);
  const [sessionStartTime, setSessionStartTime] = useState<string>('');
  const [completedModalOpen, setCompletedModalOpen] = useState<boolean>(false);
  const [completedMinutes, setCompletedMinutes] = useState<number>(0);
  const [todayTotalMinutes, setTodayTotalMinutes] = useState<number>(140);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const progress = getLocalProgress();
    // Calculate today's total studied minutes
    const todayStr = new Date().toISOString().split('T')[0];
    const todaySessions = (progress.studySessions || []).filter(s => s.startTime?.startsWith(todayStr) || s.createdAt?.startsWith(todayStr));
    const total = todaySessions.reduce((acc, s) => acc + (s.durationMinutes || 0), 0);
    setTodayTotalMinutes(total > 0 ? total : 140);
  }, [completedModalOpen]);

  useEffect(() => {
    if (isActive) {
      if (!sessionStartTime) {
        setSessionStartTime(new Date().toISOString());
      }
      timerRef.current = setInterval(() => {
        setSecondsRemaining((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current!);
            handleTimerComplete();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isActive]);

  const setTimerPreset = (minutes: number, newMode: 'Focus' | 'Short Break' | 'Long Break' = 'Focus') => {
    setIsActive(false);
    setMode(newMode);
    setTargetDurationMinutes(minutes);
    setSecondsRemaining(minutes * 60);
  };

  const handleStartPause = () => {
    setIsActive(!isActive);
  };

  const handleReset = () => {
    setIsActive(false);
    setSecondsRemaining(targetDurationMinutes * 60);
  };

  const handleTimerComplete = () => {
    setIsActive(false);
    const elapsedMinutes = targetDurationMinutes - Math.floor(secondsRemaining / 60);
    const duration = elapsedMinutes > 0 ? elapsedMinutes : targetDurationMinutes;
    setCompletedMinutes(duration);

    // Record session
    const newSession: StudySession = {
      id: 'sess-' + Date.now(),
      subject: selectedSubject,
      topic: selectedTopic,
      resourceId: initialResourceId || undefined,
      startTime: sessionStartTime || new Date(Date.now() - duration * 60000).toISOString(),
      endTime: new Date().toISOString(),
      durationMinutes: duration,
      sessionType: mode,
      completed: true,
      createdAt: new Date().toISOString()
    };
    addStudySession(newSession);

    // Update timetable item if matched
    const progress = getLocalProgress();
    if (progress.timetable) {
      const updatedTt = progress.timetable.map(t => {
        if (t.subject.toLowerCase() === selectedSubject.toLowerCase()) {
          return { ...t, completed: true };
        }
        return t;
      });
      saveLocalProgress({ timetable: updatedTt });
    }

    setCompletedModalOpen(true);
  };

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  const progressPct = ((targetDurationMinutes * 60 - secondsRemaining) / (targetDurationMinutes * 60)) * 100;

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {!isDistractionFree && (
        <div className="flex items-center justify-between border-b border-slate-150 pb-3 gap-2">
          <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto scrollbar-none no-scrollbar w-full max-w-full">
            <Link
              href="/study"
              className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-semibold bg-slate-900 text-white shadow-subtle flex-shrink-0"
            >
              Focus Timer
            </Link>
            <Link
              href="/study/today"
              className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
            >
              Today’s Plan
            </Link>
            <Link
              href="/study/timetable"
              className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
            >
              Timetable Schedule
            </Link>
            <Link
              href="/study/history"
              className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
            >
              Session History
            </Link>
          </div>

          <button
            type="button"
            onClick={() => setIsDistractionFree(true)}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
            title="Focus Mode (Distraction-Free)"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Study Mode</span>
          </button>
        </div>
      )}

      {/* Distraction Free Top Bar */}
      {isDistractionFree && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
            DISTRACTION-FREE STUDY MODE
          </span>
          <button
            type="button"
            onClick={() => setIsDistractionFree(false)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 shadow-subtle"
          >
            <Minimize2 className="w-3.5 h-3.5" />
            <span>Exit Fullscreen</span>
          </button>
        </div>
      )}

      {/* Main Focus Timer Glass Container */}
      <div className="p-8 sm:p-16 rounded-3xl bg-white/80 backdrop-blur-2xl border border-white/90 shadow-card text-center space-y-8 max-w-xl mx-auto w-full">
        {/* Mode Selector */}
        <div className="inline-flex items-center gap-1 bg-slate-100/80 p-1 rounded-full text-xs font-medium">
          <button
            type="button"
            onClick={() => setTimerPreset(25, 'Focus')}
            className={`px-3.5 py-1 rounded-full transition-smooth ${
              mode === 'Focus' && targetDurationMinutes === 25
                ? 'bg-white text-slate-900 shadow-sm font-semibold'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            25m Focus
          </button>
          <button
            type="button"
            onClick={() => setTimerPreset(50, 'Focus')}
            className={`px-3.5 py-1 rounded-full transition-smooth ${
              mode === 'Focus' && targetDurationMinutes === 50
                ? 'bg-white text-slate-900 shadow-sm font-semibold'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            50m Focus
          </button>
          <button
            type="button"
            onClick={() => setTimerPreset(5, 'Short Break')}
            className={`px-3 py-1 rounded-full transition-smooth ${
              mode === 'Short Break'
                ? 'bg-white text-slate-900 shadow-sm font-semibold'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            5m Break
          </button>
        </div>

        {/* Large Central Timer Display */}
        <div className="space-y-4 py-2">
          <div className="font-display font-extrabold text-7xl sm:text-8xl text-slate-900 tracking-tight tabular-nums select-none">
            {formattedTime}
          </div>

          {/* Thin Minimal Progress Indicator */}
          <div className="w-40 sm:w-56 h-1 bg-slate-100 rounded-full mx-auto overflow-hidden">
            <div
              className="h-full bg-slate-900 rounded-full transition-all duration-1000"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* Subject & Topic Details */}
        <div className="space-y-1 max-w-sm mx-auto">
          <div className="flex items-center justify-center">
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="font-display font-bold text-lg text-slate-900 bg-transparent border-none text-center focus:outline-none cursor-pointer"
            >
              <option value="History">Modern History</option>
              <option value="Indian Polity">Indian Polity</option>
              <option value="Geography">Geography</option>
              <option value="Economy">Economy</option>
              <option value="Current Affairs">Current Affairs</option>
              <option value="CSAT">CSAT</option>
            </select>
          </div>
          <input
            type="text"
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            placeholder="Chapter or Topic Name"
            className="w-full text-center text-xs text-slate-500 bg-transparent border-none focus:outline-none py-1"
          />
        </div>

        {/* Timer Control Buttons */}
        <div className="flex items-center justify-center gap-2 pt-2">
          <button
            type="button"
            onClick={handleStartPause}
            className={`inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-full font-semibold text-xs shadow-sm transition-smooth ${
              isActive
                ? 'bg-slate-100 hover:bg-slate-200 text-slate-900'
                : 'bg-slate-900 hover:bg-slate-800 text-white'
            }`}
          >
            {isActive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{isActive ? 'Pause' : 'Start'}</span>
          </button>

          <button
            type="button"
            onClick={handleReset}
            className="p-2.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 transition-smooth"
            title="Reset"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={handleTimerComplete}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-full bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-smooth"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Complete</span>
          </button>
        </div>
      </div>

      {/* Distraction Free Bottom Status */}
      {isDistractionFree && (
        <div className="text-center text-xs text-slate-400 font-sans">
          <span>Active focus on {selectedSubject}. Today’s total: {Math.floor(todayTotalMinutes / 60)}h {todayTotalMinutes % 60}m</span>
        </div>
      )}

      {/* Completion Modal */}
      {completedModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white max-w-md w-full rounded-4xl p-8 shadow-command border border-slate-200 space-y-6 text-center animate-in zoom-in-95">
            <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto text-xl">
              ✓
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                SESSION RECORDED
              </span>
              <h3 className="font-display font-bold text-2xl text-slate-900">
                Session Complete.
              </h3>
              <p className="text-sm text-slate-500 font-sans">
                {completedMinutes} minutes focused on <strong className="text-slate-900">{selectedSubject}</strong>.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-150 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Today’s Total Focused Time:</span>
                <span className="font-semibold text-slate-900">{Math.floor((todayTotalMinutes + completedMinutes) / 60)}h {(todayTotalMinutes + completedMinutes) % 60}m</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Subject:</span>
                <span>{selectedSubject}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => { setCompletedModalOpen(false); setTimerPreset(targetDurationMinutes); }}
                className="flex-1 py-3 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors"
              >
                Another Session
              </button>
              <button
                type="button"
                onClick={() => { setCompletedModalOpen(false); router.push('/study/today'); }}
                className="flex-1 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-colors"
              >
                Back to Today's Plan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function StudyTimerPage() {
  return (
    <Suspense fallback={
      <div className="max-w-4xl mx-auto px-4 py-32 text-center space-y-2">
        <div className="w-6 h-6 rounded-full border-2 border-slate-900 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-slate-400 font-medium">Initializing Focus Timer...</p>
      </div>
    }>
      <StudyTimerContent />
    </Suspense>
  );
}

