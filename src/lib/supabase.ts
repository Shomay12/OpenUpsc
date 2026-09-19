import { createClient } from '@supabase/supabase-js';
import { UserProfile, StudySession, TimetableEvent } from './types';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

// Default demo profile for seamless offline/local use
export const DEFAULT_PROFILE: UserProfile = {
  id: 'usr-default-student',
  name: 'Khushi',
  email: 'student@upschub.in',
  avatarUrl: '',
  preparationStage: 'Foundation (Class 6-12)',
  targetAttemptYear: '2028',
  dailyTargetHours: 4,
  createdAt: '2026-01-01'
};

// Initial default timetable schedule
export const DEFAULT_TIMETABLE: TimetableEvent[] = [
  {
    id: 'tt-1',
    dayOfWeek: 'Daily',
    startTime: '06:30',
    endTime: '07:30',
    subject: 'History',
    topic: 'Modern Indian History (Revolt of 1857)',
    resourceId: 'res-ncert-history-mega',
    resourceTitle: 'Complete NCERT History Class 6–12',
    completed: true
  },
  {
    id: 'tt-2',
    dayOfWeek: 'Daily',
    startTime: '08:00',
    endTime: '09:00',
    subject: 'Indian Polity',
    topic: 'Indian Constitution at Work (Fundamental Rights)',
    resourceId: 'res-ncert-polity-strategy',
    resourceTitle: 'NCERT Indian Polity Foundation',
    completed: false
  },
  {
    id: 'tt-3',
    dayOfWeek: 'Daily',
    startTime: '18:00',
    endTime: '19:00',
    subject: 'Current Affairs',
    topic: 'Daily Editorial & PIB Summary',
    resourceId: 'res-pib-portal',
    resourceTitle: 'PIB Government Releases',
    completed: false
  },
  {
    id: 'tt-4',
    dayOfWeek: 'Daily',
    startTime: '20:00',
    endTime: '21:00',
    subject: 'Geography',
    topic: 'Physical Geography & River Systems',
    resourceId: 'res-ncert-geo-mega',
    resourceTitle: 'NCERT Geography Class 6–12',
    completed: false
  }
];

// Initial demo study sessions for history/analytics
export const DEFAULT_SESSIONS: StudySession[] = [
  {
    id: 'sess-1',
    subject: 'History',
    topic: 'Modern Indian History',
    durationMinutes: 60,
    startTime: new Date(Date.now() - 3600000 * 4).toISOString(),
    endTime: new Date(Date.now() - 3600000 * 3).toISOString(),
    sessionType: 'Focus',
    completed: true,
    createdAt: new Date().toISOString()
  },
  {
    id: 'sess-2',
    subject: 'Indian Polity',
    topic: 'Constitutional Morality & Preamble',
    durationMinutes: 50,
    startTime: new Date(Date.now() - 3600000 * 2).toISOString(),
    endTime: new Date(Date.now() - 3600000 * 1.1).toISOString(),
    sessionType: 'Focus',
    completed: true,
    createdAt: new Date().toISOString()
  },
  {
    id: 'sess-3',
    subject: 'Current Affairs',
    topic: 'PIB Core Sector & Inflation Analysis',
    durationMinutes: 30,
    startTime: new Date(Date.now() - 3600000 * 24).toISOString(),
    endTime: new Date(Date.now() - 3600000 * 23.5).toISOString(),
    sessionType: 'Focus',
    completed: true,
    createdAt: new Date(Date.now() - 86400000).toISOString()
  }
];
