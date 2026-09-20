'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { createClient } from '../utils/supabase/client';
import { UserProfile } from '../lib/types';
import { DEFAULT_PROFILE } from '../lib/supabase';
import { getLocalProgress, saveLocalProgress } from '../lib/store';

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signInWithEmail: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signUpWithEmail: (email: string, password: string, fullName: string) => Promise<{ error: AuthError | null; user: User | null }>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  resetPasswordForEmail: (email: string) => Promise<{ error: AuthError | null }>;
  updatePassword: (password: string) => Promise<{ error: AuthError | null }>;
  updateProfile: (data: Partial<UserProfile>) => Promise<boolean>;
  deleteAccount: () => Promise<boolean>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch or create profile for authenticated user
  const fetchProfile = async (currentUser: User) => {
    try {
      const { data } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', currentUser.id)
        .single();

      const nameFallback = 
        currentUser.user_metadata?.full_name || 
        currentUser.user_metadata?.name || 
        currentUser.email?.split('@')[0] || 
        'Aspirant';

      const avatarFallback = 
        currentUser.user_metadata?.avatar_url || 
        currentUser.user_metadata?.picture || 
        '';

      if (data) {
        const loadedProfile: UserProfile = {
          id: data.id,
          name: data.full_name || nameFallback,
          email: currentUser.email || '',
          avatarUrl: data.avatar_url || avatarFallback,
          preparationStage: data.preparation_stage || 'Foundation (Class 6-12)',
          targetAttemptYear: data.target_attempt || '2028',
          dailyTargetHours: data.daily_study_target || 4,
          createdAt: data.created_at || new Date().toISOString()
        };
        setProfile(loadedProfile);
        saveLocalProgress({ profile: loadedProfile });
      } else {
        // Fallback / Initial profile
        const newProf: UserProfile = {
          id: currentUser.id,
          name: nameFallback,
          email: currentUser.email || '',
          avatarUrl: avatarFallback,
          preparationStage: 'Foundation (Class 6-12)',
          targetAttemptYear: '2028',
          dailyTargetHours: 4,
          createdAt: new Date().toISOString()
        };
        setProfile(newProf);
        saveLocalProgress({ profile: newProf });

        // Upsert to Supabase
        await supabase.from('profiles').upsert({
          id: currentUser.id,
          full_name: newProf.name,
          avatar_url: newProf.avatarUrl,
          preparation_stage: newProf.preparationStage,
          target_attempt: newProf.targetAttemptYear,
          daily_study_target: newProf.dailyTargetHours,
          updated_at: new Date().toISOString()
        });
      }
    } catch (err) {
      console.log('Profile fetch notice:', err);
      const fallback = getLocalProgress().profile || DEFAULT_PROFILE;
      setProfile(fallback);
    }
  };

  useEffect(() => {
    // Initial session retrieval & OAuth code fallback exchange
    const initializeAuth = async () => {
      try {
        // Fallback: If URL has ?code= (e.g. from Google OAuth direct redirect to / or other routes)
        if (typeof window !== 'undefined') {
          const urlParams = new URLSearchParams(window.location.search);
          const code = urlParams.get('code');
          if (code) {
            try {
              const { data, error } = await supabase.auth.exchangeCodeForSession(code);
              if (!error && data?.session) {
                setSession(data.session);
                setUser(data.session.user);
                if (data.session.user) {
                  await fetchProfile(data.session.user);
                }
                // Clean the code param from current URL
                urlParams.delete('code');
                const cleanSearch = urlParams.toString();
                const newUrl = window.location.pathname + (cleanSearch ? `?${cleanSearch}` : '') + window.location.hash;
                window.history.replaceState({}, document.title, newUrl);
                setIsLoading(false);
                return;
              }
            } catch (exchangeErr) {
              console.warn('OAuth code client exchange notice:', exchangeErr);
            }
          }
        }

        const { data: { session: initialSession } } = await supabase.auth.getSession();
        setSession(initialSession);
        setUser(initialSession?.user ?? null);

        if (initialSession?.user) {
          await fetchProfile(initialSession.user);
        } else {
          // Check local progress for offline mode
          const local = getLocalProgress();
          if (local.profile) {
            setProfile(local.profile);
          }
        }
      } catch (e) {
        console.log('Auth initialization skipped/offline:', e);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen to real-time auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        setSession(newSession);
        setUser(newSession?.user ?? null);

        if (newSession?.user) {
          await fetchProfile(newSession.user);
        } else {
          setProfile(null);
        }
        setIsLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase]);

  const signInWithEmail = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      if (data.user) {
        setUser(data.user);
        setSession(data.session);
        await fetchProfile(data.user);
      }
      return { error: null };
    } catch (err: any) {
      return { error: err };
    } finally {
      setIsLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, password: string, fullName: string) => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });
      if (error) throw error;
      if (data.user) {
        setUser(data.user);
        setSession(data.session);
        // Create initial profile
        const initialProfile: UserProfile = {
          id: data.user.id,
          name: fullName || email.split('@')[0],
          email: email,
          preparationStage: 'Foundation (Class 6-12)',
          targetAttemptYear: '2028',
          dailyTargetHours: 4,
          createdAt: new Date().toISOString()
        };
        setProfile(initialProfile);
        saveLocalProgress({ profile: initialProfile });

        await supabase.from('profiles').upsert({
          id: data.user.id,
          full_name: fullName,
          preparation_stage: 'Foundation (Class 6-12)',
          target_attempt: '2028',
          daily_study_target: 4,
          updated_at: new Date().toISOString()
        });
      }
      return { error: null, user: data.user };
    } catch (err: any) {
      return { error: err, user: null };
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = async () => {
    try {
      const redirectOrigin = typeof window !== 'undefined' ? window.location.origin : '';
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${redirectOrigin}/auth/callback?next=/dashboard`,
          queryParams: {
            prompt: 'select_account',
          },
        },
      });
      if (error) throw error;
    } catch (err: any) {
      console.error('Google OAuth error:', err);
      throw err;
    }
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      await supabase.auth.signOut();
      setUser(null);
      setSession(null);
      setProfile(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('upsc_hub_auth_user_v1');
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPasswordForEmail = async (email: string) => {
    try {
      const redirectOrigin = typeof window !== 'undefined' ? window.location.origin : '';
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${redirectOrigin}/auth/callback?next=/auth/reset-password`,
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const updatePassword = async (password: string) => {
    try {
      const { error } = await supabase.auth.updateUser({ password });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const updateProfileData = async (data: Partial<UserProfile>): Promise<boolean> => {
    try {
      const current = profile || DEFAULT_PROFILE;
      const updated: UserProfile = {
        ...current,
        ...data,
      };
      setProfile(updated);
      saveLocalProgress({ profile: updated });

      if (user) {
        await supabase.from('profiles').upsert({
          id: user.id,
          full_name: updated.name,
          preparation_stage: updated.preparationStage,
          target_attempt: updated.targetAttemptYear,
          daily_study_target: updated.dailyTargetHours,
          updated_at: new Date().toISOString()
        });
      }
      return true;
    } catch (err) {
      console.error('Update profile error:', err);
      return false;
    }
  };

  const deleteAccount = async (): Promise<boolean> => {
    try {
      if (user) {
        // Delete user tables records in Supabase (profiles cascades to other tables)
        await supabase.from('profiles').delete().eq('id', user.id);
        await signOut();
      }
      return true;
    } catch (err) {
      console.error('Delete account error:', err);
      return false;
    }
  };

  const refreshProfile = async () => {
    if (user) {
      await fetchProfile(user);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        session,
        isLoading,
        isAuthenticated: Boolean(user || (profile && profile.id !== 'usr-default-student')),
        signInWithEmail,
        signUpWithEmail,
        signInWithGoogle,
        signOut,
        resetPasswordForEmail,
        updatePassword,
        updateProfile: updateProfileData,
        deleteAccount,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
