'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Sparkles,
  Lock,
  Mail,
  User as UserIcon,
  KeyRound,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

function AuthFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get('next') || '/dashboard';
  const initialMode = searchParams.get('mode') === 'signup' ? 'signup' : 'login';

  const { 
    user, 
    signInWithEmail, 
    signUpWithEmail, 
    signInWithGoogle, 
    resetPasswordForEmail, 
    isLoading 
  } = useAuth();

  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user && !isLoading) {
      router.push(nextUrl);
    }
  }, [user, isLoading, router, nextUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);

    try {
      if (mode === 'signup') {
        if (password !== confirmPassword) {
          setError('Passwords do not match.');
          setSubmitting(false);
          return;
        }
        if (password.length < 6) {
          setError('Password must be at least 6 characters.');
          setSubmitting(false);
          return;
        }

        const { error: signUpError, user: newUser } = await signUpWithEmail(email, password, name);
        if (signUpError) {
          if (signUpError.message.includes('already registered')) {
            setError('An account with this email already exists. Please log in.');
          } else {
            setError(signUpError.message || 'Unable to create account. Please check your details.');
          }
        } else {
          // If session created, redirect to onboarding
          router.push('/onboarding');
        }
      } else if (mode === 'login') {
        const { error: signInError } = await signInWithEmail(email, password);
        if (signInError) {
          if (signInError.message.includes('Invalid login credentials')) {
            setError('Incorrect email or password. Please try again.');
          } else {
            setError(signInError.message || 'Unable to sign in. Please verify your credentials.');
          }
        } else {
          router.push(nextUrl);
        }
      } else if (mode === 'forgot') {
        const { error: resetError } = await resetPasswordForEmail(email);
        if (resetError) {
          setError(resetError.message || 'Unable to send password reset link. Please check the email.');
        } else {
          setMessage('Password reset instructions have been sent to your email.');
        }
      }
    } catch (err: any) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pt-24 sm:pt-32 pb-24 max-w-md mx-auto px-4 sm:px-6 space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center font-display font-bold text-sm mx-auto shadow-subtle">
          U
        </div>
        <h1 className="font-display font-extrabold text-2xl sm:text-3xl text-slate-900 tracking-tight">
          {mode === 'signup'
            ? 'Create your account'
            : mode === 'forgot'
            ? 'Reset password'
            : 'Welcome back'}
        </h1>
        <p className="text-xs text-slate-500 font-sans">
          {mode === 'signup'
            ? 'Build your personal UPSC preparation workspace.'
            : mode === 'forgot'
            ? 'Enter your email to receive a password reset link.'
            : 'Continue your UPSC preparation journey.'}
        </p>
      </div>

      {/* Main Form Container */}
      <div className="p-8 rounded-4xl bg-white border border-slate-200/80 shadow-card space-y-6">
        {/* Google OAuth Button */}
        {mode !== 'forgot' && (
          <>
            <button
              type="button"
              onClick={signInWithGoogle}
              className="w-full inline-flex items-center justify-center gap-2.5 py-3.5 rounded-full border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-smooth"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>

            <div className="flex items-center gap-3 text-slate-300 text-xs font-sans">
              <div className="flex-1 h-px bg-slate-150" />
              <span>or email</span>
              <div className="flex-1 h-px bg-slate-150" />
            </div>
          </>
        )}

        {/* Error / Success Alerts */}
        {error && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {message && (
          <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {/* Email & Password Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
          {mode === 'signup' && (
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Aarav Sharma"
                className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
              />
            </div>
          )}

          <div className="space-y-1">
            <label className="font-semibold text-slate-700">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full p-3.5 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
            />
          </div>

          {mode !== 'forgot' && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-slate-700">Password</label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => { setMode('forgot'); setError(null); setMessage(null); }}
                    className="text-[11px] text-slate-500 hover:text-slate-900 font-medium"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
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
          )}

          {mode === 'signup' && (
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Confirm Password</label>
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
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-subtle transition-smooth flex items-center justify-center gap-2"
          >
            <span>
              {submitting
                ? 'Processing...'
                : mode === 'signup'
                ? 'Create Account'
                : mode === 'forgot'
                ? 'Send Reset Link'
                : 'Log In'}
            </span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Toggle Links */}
        <div className="text-center pt-2 space-y-1">
          {mode === 'login' && (
            <button
              type="button"
              onClick={() => { setMode('signup'); setError(null); setMessage(null); }}
              className="text-xs text-slate-500 hover:text-slate-900 font-medium"
            >
              Don’t have an account? <strong className="text-slate-900 font-semibold">Create account</strong>
            </button>
          )}

          {mode === 'signup' && (
            <button
              type="button"
              onClick={() => { setMode('login'); setError(null); setMessage(null); }}
              className="text-xs text-slate-500 hover:text-slate-900 font-medium"
            >
              Already have an account? <strong className="text-slate-900 font-semibold">Log in</strong>
            </button>
          )}

          {mode === 'forgot' && (
            <button
              type="button"
              onClick={() => { setMode('login'); setError(null); setMessage(null); }}
              className="text-xs text-slate-500 hover:text-slate-900 font-medium"
            >
              Remember password? <strong className="text-slate-900 font-semibold">Back to log in</strong>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <Suspense fallback={
      <div className="max-w-md mx-auto px-4 py-32 text-center space-y-2">
        <div className="w-6 h-6 rounded-full border-2 border-slate-900 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-slate-400 font-medium">Loading workspace...</p>
      </div>
    }>
      <AuthFormContent />
    </Suspense>
  );
}
