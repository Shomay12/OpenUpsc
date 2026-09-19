'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';

export default function ResetPasswordPage() {
  const router = useRouter();
  const { updatePassword } = useAuth();
  
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    setError(null);

    const { error: updateErr } = await updatePassword(newPassword);
    if (updateErr) {
      setError(updateErr.message || 'Unable to update password. Link may have expired.');
    } else {
      setSuccess(true);
      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
    }
    setLoading(false);
  };

  return (
    <div className="pt-24 sm:pt-32 pb-24 max-w-md mx-auto px-4 sm:px-6 space-y-8 animate-in fade-in duration-200">
      <div className="text-center space-y-2">
        <div className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center font-display font-bold text-sm mx-auto shadow-subtle">
          <Lock className="w-4 h-4" />
        </div>
        <h1 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900 tracking-tight">
          Set New Password
        </h1>
        <p className="text-xs text-slate-500 font-sans">
          Enter and confirm your new account password.
        </p>
      </div>

      <div className="p-8 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
        {error && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs text-center space-y-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto" />
            <p className="font-semibold text-sm">Password updated successfully!</p>
            <p className="text-[11px] text-emerald-700">Redirecting you to your personal dashboard...</p>
          </div>
        ) : (
          <form onSubmit={handleUpdate} className="space-y-4 text-xs font-sans">
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">New Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
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

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-subtle transition-smooth flex items-center justify-center gap-2"
            >
              <span>{loading ? 'Updating Password...' : 'Save New Password'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
