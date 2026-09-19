'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  Plus, 
  Trash2, 
  Edit3, 
  Play, 
  Calendar, 
  CheckCircle2, 
  Save, 
  X,
  Clock
} from 'lucide-react';
import { TimetableEvent } from '../../../lib/types';
import { getLocalProgress, saveLocalProgress } from '../../../lib/store';
import SeniorGuidanceBox from '../../../components/SeniorGuidanceBox';

export default function TimetablePage() {
  const router = useRouter();
  const [timetable, setTimetable] = useState<TimetableEvent[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState<Partial<TimetableEvent>>({
    dayOfWeek: 'Daily',
    startTime: '06:30',
    endTime: '07:30',
    subject: 'History',
    topic: 'Modern Indian History',
    resourceTitle: 'Complete NCERT History'
  });

  useEffect(() => {
    const progress = getLocalProgress();
    setTimetable(progress.timetable || []);
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    let updated: TimetableEvent[];
    if (editingId) {
      updated = timetable.map(item => item.id === editingId ? { ...item, ...formData } as TimetableEvent : item);
    } else {
      const newEvent: TimetableEvent = {
        id: 'tt-' + Date.now(),
        dayOfWeek: formData.dayOfWeek || 'Daily',
        startTime: formData.startTime || '08:00',
        endTime: formData.endTime || '09:00',
        subject: formData.subject || 'History',
        topic: formData.topic || 'General Topic',
        resourceTitle: formData.resourceTitle,
        completed: false
      };
      updated = [...timetable, newEvent];
    }
    setTimetable(updated);
    saveLocalProgress({ timetable: updated });
    setIsAdding(false);
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    const updated = timetable.filter(t => t.id !== id);
    setTimetable(updated);
    saveLocalProgress({ timetable: updated });
  };

  const startSession = (item: TimetableEvent) => {
    router.push(`/study?subject=${encodeURIComponent(item.subject)}&topic=${encodeURIComponent(item.topic)}&duration=50`);
  };

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none no-scrollbar w-full max-w-full border-b border-slate-150 pb-3">
        <Link
          href="/study"
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex-shrink-0"
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
          className="px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-semibold bg-slate-900 text-white shadow-subtle flex-shrink-0"
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

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            RECURRING SCHEDULE
          </span>
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
            My Study Plan
          </h1>
        </div>

        <button
          type="button"
          onClick={() => { setIsAdding(true); setEditingId(null); }}
          className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-subtle transition-smooth"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Study Block</span>
        </button>
      </div>

      {/* Add / Edit Block Modal */}
      {isAdding && (
        <div className="p-8 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6 animate-in zoom-in-95">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-display font-bold text-lg text-slate-900">
              {editingId ? 'Edit Study Block' : 'Add New Recurring Block'}
            </h3>
            <button
              onClick={() => { setIsAdding(false); setEditingId(null); }}
              className="text-xs text-slate-400 hover:text-slate-700"
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleSave} className="space-y-4 text-xs font-sans">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Subject</label>
                <select
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                >
                  <option value="History">History</option>
                  <option value="Indian Polity">Indian Polity</option>
                  <option value="Geography">Geography</option>
                  <option value="Economy">Economy</option>
                  <option value="Current Affairs">Current Affairs</option>
                  <option value="CSAT">CSAT</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Day</label>
                <select
                  value={formData.dayOfWeek}
                  onChange={(e) => setFormData({ ...formData, dayOfWeek: e.target.value as any })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                >
                  <option value="Daily">Daily</option>
                  <option value="Monday">Monday</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                  <option value="Saturday">Saturday</option>
                  <option value="Sunday">Sunday</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Start Time</label>
                <input
                  type="time"
                  value={formData.startTime || '06:30'}
                  onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">End Time</label>
                <input
                  type="time"
                  value={formData.endTime || '07:30'}
                  onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label className="font-semibold text-slate-700">Topic / Focus Chapter</label>
                <input
                  type="text"
                  required
                  value={formData.topic || ''}
                  onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  placeholder="e.g. Modern Indian History / Revolt of 1857"
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label className="font-semibold text-slate-700">Assigned Resource Title (Optional)</label>
                <input
                  type="text"
                  value={formData.resourceTitle || ''}
                  onChange={(e) => setFormData({ ...formData, resourceTitle: e.target.value })}
                  placeholder="e.g. Spectrum Chapter 4 / NCERT Class 8"
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => { setIsAdding(false); setEditingId(null); }}
                className="px-4 py-2 rounded-full text-slate-500 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2.5 rounded-full bg-slate-900 text-white font-medium text-xs shadow-subtle"
              >
                Save Block
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Timetable Blocks Stack */}
      <div className="space-y-3">
        {timetable.map((block) => (
          <div
            key={block.id}
            className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-subtle hover:shadow-cardHover transition-smooth flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold text-slate-400">
                  {block.startTime} – {block.endTime}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                  {block.subject}
                </span>
                <span className="text-[10px] text-slate-400">
                  {block.dayOfWeek}
                </span>
              </div>
              <h4 className="font-display font-bold text-base text-slate-900">
                {block.topic}
              </h4>
              {block.resourceTitle && (
                <p className="text-xs text-slate-400 font-sans">
                  Assigned Resource: {block.resourceTitle}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 self-end sm:self-center">
              <button
                type="button"
                onClick={() => startSession(block)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-subtle transition-smooth"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>Start</span>
              </button>
              <button
                type="button"
                onClick={() => { setEditingId(block.id); setFormData(block); setIsAdding(true); }}
                className="p-2 rounded-full text-slate-400 hover:text-slate-900"
              >
                <Edit3 className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => handleDelete(block.id)}
                className="p-2 rounded-full text-slate-400 hover:text-rose-600"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
