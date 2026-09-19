'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  User, 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Trash2, 
  Save, 
  Check, 
  Lock, 
  LogOut, 
  Globe, 
  Clock, 
  AlertTriangle 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function SettingsPage() {
  const router = useRouter();
  const { profile, user, updateProfile, updatePassword, signOut, deleteAccount, refreshProfile } = useAuth();

  const [activeTab, setActiveTab] = useState<'account' | 'preferences' | 'security'>('account');
  const [name, setName] = useState(profile?.name || '');
  const [dailyHours, setDailyHours] = useState(profile?.dailyTargetHours || 4);
  const [prepStage, setPrepStage] = useState(profile?.preparationStage || 'Foundation (Class 6-12)');
  const [targetYear, setTargetYear] = useState(profile?.targetAttemptYear || '2028');
  
  // Password change state
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Status
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await updateProfile({
      name,
      dailyTargetHours: dailyHours,
      preparationStage: prepStage,
      targetAttemptYear: targetYear,
    });
    if (success) {
      setSavedSuccess(true);
      await refreshProfile();
      setTimeout(() => setSavedSuccess(false), 2500);
    }
  };

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);
    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters.');
      return;
    }

    const { error } = await updatePassword(password);
    if (error) {
      setPasswordError(error.message || 'Unable to update password.');
    } else {
      setPasswordMessage('Password updated successfully.');
      setPassword('');
      setConfirmPassword('');
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    const ok = await deleteAccount();
    if (ok) {
      router.push('/');
    } else {
      setDeleting(false);
      setShowDeleteModal(false);
    }
  };

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          WORKSPACE SETTINGS
        </span>
        <h1 className="font-display font-extrabold text-2xl sm:text-4xl text-slate-900 tracking-tight">
          Account & Preferences
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 font-sans">
          Manage your personal profile, study preferences, and account security.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-150 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('account')}
          className={`px-4 py-2 rounded-full text-xs font-semibold transition-smooth ${
            activeTab === 'account'
              ? 'bg-slate-900 text-white shadow-subtle'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          Account Info
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('preferences')}
          className={`px-4 py-2 rounded-full text-xs font-semibold transition-smooth ${
            activeTab === 'preferences'
              ? 'bg-slate-900 text-white shadow-subtle'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          Study Preferences
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2 rounded-full text-xs font-semibold transition-smooth ${
            activeTab === 'security'
              ? 'bg-slate-900 text-white shadow-subtle'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          Security & Danger Zone
        </button>
      </div>

      {/* TAB 1: ACCOUNT INFO */}
      {activeTab === 'account' && (
        <form onSubmit={handleSaveProfile} className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <h3 className="font-display font-bold text-lg text-slate-900">Personal Details</h3>
            {savedSuccess && (
              <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Saved
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-sans">
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
              />
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Email Address (Read Only)</label>
              <input
                type="email"
                disabled
                value={user?.email || profile?.email || ''}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-100 text-slate-500 cursor-not-allowed"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button
              type="submit"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: STUDY PREFERENCES */}
      {activeTab === 'preferences' && (
        <form onSubmit={handleSaveProfile} className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-150">
            <h3 className="font-display font-bold text-lg text-slate-900">Preparation & Study Target</h3>
            {savedSuccess && (
              <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Saved
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Preparation Stage</label>
              <select
                value={prepStage}
                onChange={(e) => setPrepStage(e.target.value)}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
              >
                <option value="Foundation (Class 6-12)">Foundation (Class 6-12)</option>
                <option value="Standard Reference Core">Standard Reference Core</option>
                <option value="Advanced / Current Affairs">Advanced / Current Affairs</option>
                <option value="Exam Practice / PYQs">Exam Practice / PYQs</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Target Attempt Year</label>
              <select
                value={targetYear}
                onChange={(e) => setTargetYear(e.target.value)}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
              >
                <option value="2026">2026</option>
                <option value="2027">2027</option>
                <option value="2028">2028</option>
                <option value="2029">2029</option>
                <option value="2030">2030</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Daily Study Target</label>
              <select
                value={dailyHours}
                onChange={(e) => setDailyHours(Number(e.target.value))}
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
              >
                <option value={2}>2 Hours / Day</option>
                <option value={3}>3 Hours / Day</option>
                <option value={4}>4 Hours / Day</option>
                <option value={6}>6 Hours / Day</option>
                <option value={8}>8 Hours / Day</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button
              type="submit"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Update Preferences</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 3: SECURITY & DANGER ZONE */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          {/* Password Change Box */}
          <form onSubmit={handlePasswordUpdate} className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-4">
            <h3 className="font-display font-bold text-lg text-slate-900">Change Password</h3>

            {passwordError && (
              <div className="p-3 rounded-2xl bg-rose-50 text-rose-800 text-xs">{passwordError}</div>
            )}
            {passwordMessage && (
              <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-800 text-xs">{passwordMessage}</div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-sans">
              <div className="space-y-1">
                <label className="font-semibold text-slate-700">New Password</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Confirm New Password</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="px-6 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
              >
                Update Password
              </button>
            </div>
          </form>

          {/* Logout All / Current */}
          <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card flex items-center justify-between gap-4">
            <div>
              <h4 className="font-display font-bold text-sm text-slate-900">Session Management</h4>
              <p className="text-xs text-slate-500 font-sans">Log out from your current active session.</p>
            </div>
            <button
              type="button"
              onClick={async () => { await signOut(); router.push('/auth'); }}
              className="px-5 py-2.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-smooth"
            >
              Log Out
            </button>
          </div>

          {/* Delete Account Danger Zone */}
          <div className="p-6 sm:p-8 rounded-2xl bg-rose-50/60 border border-rose-200 text-rose-950 space-y-4">
            <div className="flex items-center gap-2 text-rose-900 font-display font-bold text-sm">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>Danger Zone</span>
            </div>
            <p className="text-xs text-rose-800/80 font-sans leading-relaxed">
              Permanently delete your account and all associated personal progress, study sessions, notes, and timetable records. Shared public resources will not be affected.
            </p>
            <button
              type="button"
              onClick={() => setShowDeleteModal(true)}
              className="px-5 py-2.5 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-subtle transition-smooth"
            >
              Delete Account
            </button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 sm:p-7 shadow-2xl border border-slate-200 space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
              <Trash2 className="w-5 h-5" />
            </div>

            <div className="text-center space-y-1.5">
              <h3 className="font-display font-bold text-lg text-slate-900">
                Delete your account?
              </h3>
              <p className="text-xs text-slate-500 font-sans leading-relaxed">
                This will permanently delete your profile, progress, timetable, saved resources, and study history. This action cannot be undone.
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-3 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="flex-1 py-3 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold"
              >
                {deleting ? 'Deleting...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
