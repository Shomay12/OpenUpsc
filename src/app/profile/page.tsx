'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  User, 
  Settings, 
  Save, 
  CheckCircle2, 
  Calendar, 
  Clock, 
  Target, 
  ShieldCheck,
  Sparkles,
  LogOut
} from 'lucide-react';
import { UserProfile } from '../../lib/types';
import { getLocalProgress, saveLocalProgress } from '../../lib/store';
import { DEFAULT_PROFILE } from '../../lib/supabase';

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<UserProfile>(DEFAULT_PROFILE);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    const progress = getLocalProgress();
    if (progress.profile) {
      setProfile(progress.profile);
      setFormData(progress.profile);
    }
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setProfile(formData);
    saveLocalProgress({ profile: formData });
    setIsEditing(false);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="w-full max-w-3xl space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">
          Account & Preferences
        </span>
        <h1 className="font-display font-extrabold text-3xl text-slate-900 tracking-tight">
          Profile
        </h1>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Profile updated successfully.</span>
        </div>
      )}

      {/* Subtle Glass Profile Panel */}
      {!isEditing ? (
        <div className="p-7 sm:p-9 rounded-3xl bg-white/85 backdrop-blur-xl border border-white/80 shadow-card space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-5">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-display font-bold text-lg shadow-sm">
                {profile.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h2 className="font-display font-bold text-lg text-slate-900">{profile.name}</h2>
                <p className="text-xs text-slate-400 font-sans">{profile.email}</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="px-4 py-1.5 rounded-full border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-sans">
            <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-slate-400 font-mono text-[10px] block uppercase">Preparation Stage</span>
              <p className="font-semibold text-slate-900">{profile.preparationStage}</p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-slate-400 font-mono text-[10px] block uppercase">Daily Target</span>
              <p className="font-semibold text-slate-900">{profile.dailyTargetHours} Hours</p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-slate-400 font-mono text-[10px] block uppercase">Target Attempt</span>
              <p className="font-semibold text-slate-900">UPSC {profile.targetAttemptYear}</p>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-[11px]">OpenUPSC Workspace</span>
            <Link href="/settings" className="text-slate-700 hover:text-slate-900 font-medium">
              Manage Security & Settings →
            </Link>
          </div>
        </div>
      ) : (
        /* Edit Profile Form */
        <div className="p-8 sm:p-10 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h3 className="font-display font-bold text-lg text-slate-900">
              Edit Aspirant Profile
            </h3>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="text-xs text-slate-400 hover:text-slate-700 font-medium"
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleSave} className="space-y-4 text-xs font-sans">
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Display Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
              />
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Preparation Stage</label>
              <select
                value={formData.preparationStage}
                onChange={(e) => setFormData({ ...formData, preparationStage: e.target.value as any })}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
              >
                <option value="Zero Foundation">Zero Foundation (Starting Fresh)</option>
                <option value="Foundation (Class 6-12)">Foundation (Class 6-12 NCERTs)</option>
                <option value="Standard Core">Standard Core (Laxmikanth, Spectrum, Mrunal)</option>
                <option value="Prelims Focused">Prelims Focused (Test Series & High Yield)</option>
                <option value="Mains Focused">Mains Focused (Answer Writing & Optional)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Daily Study Target (Hours)</label>
                <input
                  type="number"
                  min={1}
                  max={14}
                  value={formData.dailyTargetHours}
                  onChange={(e) => setFormData({ ...formData, dailyTargetHours: Number(e.target.value) })}
                  className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Target Year</label>
                <select
                  value={formData.targetAttemptYear}
                  onChange={(e) => setFormData({ ...formData, targetAttemptYear: e.target.value })}
                  className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none"
                >
                  <option value="2027">UPSC CSE 2027</option>
                  <option value="2028">UPSC CSE 2028</option>
                  <option value="2029">UPSC CSE 2029</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-full text-slate-500 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2.5 rounded-full bg-slate-900 text-white font-medium text-xs shadow-subtle"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
