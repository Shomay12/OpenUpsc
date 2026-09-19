'use client';

import React, { useState, useEffect } from 'react';
import { X, Save, Edit3, Check, Trash2 } from 'lucide-react';
import { getLocalProgress, saveLocalProgress } from '../lib/store';

interface NotesModalProps {
  isOpen: boolean;
  onClose: () => void;
  itemId: string;
  itemTitle: string;
  itemCategory?: string;
}

export default function NotesModal({
  isOpen,
  onClose,
  itemId,
  itemTitle,
  itemCategory = 'Study Note'
}: NotesModalProps) {
  const [noteContent, setNoteContent] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen && itemId) {
      const progress = getLocalProgress();
      setNoteContent(progress.notes[itemId] || '');
      setSavedSuccess(false);
    }
  }, [isOpen, itemId]);

  if (!isOpen) return null;

  const handleSave = () => {
    const progress = getLocalProgress();
    const updatedNotes = { ...progress.notes, [itemId]: noteContent };
    saveLocalProgress({ notes: updatedNotes });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  const handleDelete = () => {
    const progress = getLocalProgress();
    const updatedNotes = { ...progress.notes };
    delete updatedNotes[itemId];
    saveLocalProgress({ notes: updatedNotes });
    setNoteContent('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white w-full max-w-xl rounded-2xl shadow-elevation border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-navy-900 text-amber-300 flex items-center justify-center">
              <Edit3 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700">{itemCategory}</span>
              <h3 className="font-serif font-bold text-slate-900 text-base line-clamp-1">
                {itemTitle}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-6 space-y-3 flex-1 overflow-y-auto">
          <label className="block text-xs font-semibold text-slate-600">
            Personal Senior Aspirant Notes & Summary Points (Markdown supported):
          </label>
          <textarea
            value={noteContent}
            onChange={(e) => setNoteContent(e.target.value)}
            placeholder="Write key memory triggers, important article numbers, confusing keywords, or revision notes here..."
            className="w-full h-48 sm:h-64 p-3.5 rounded-xl border border-slate-200 bg-parchment-50 font-sans text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-navy-900/30 focus:border-navy-900 resize-none placeholder:text-slate-400"
          />
          <p className="text-[11px] text-slate-500">
            🔒 Saved locally in your browser storage. You can access all your notes in the <span className="font-semibold text-navy-900">My Dashboard</span> tab.
          </p>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button
            type="button"
            onClick={handleDelete}
            disabled={!noteContent}
            className="inline-flex items-center gap-1.5 text-xs text-rose-600 hover:text-rose-700 disabled:opacity-30 disabled:pointer-events-none px-2 py-1 rounded"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Note</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Close
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-navy-900 hover:bg-navy-800 text-amber-300 font-semibold text-xs shadow-sm transition-colors"
            >
              {savedSuccess ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-300">Saved!</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Note</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
