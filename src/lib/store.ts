import { UserProgressState, UserGeneratedPlan, Resource, UserProfile, StudySession, TimetableEvent } from './types';
import { INITIAL_RESOURCES } from '../data/initialResources';
import { DEFAULT_PROFILE, DEFAULT_TIMETABLE, DEFAULT_SESSIONS, supabase, isSupabaseConfigured } from './supabase';

const STORAGE_KEY = 'upsc_resource_hub_user_progress_v2';
const CUSTOM_RESOURCES_KEY = 'upsc_resource_hub_custom_resources_v1';
const AUTH_USER_KEY = 'upsc_hub_auth_user_v1';

export const DEFAULT_PROGRESS: UserProgressState = {
  completedResourceIds: ['res-ncert-history-mega'],
  inProgressResourceIds: ['res-ncert-polity-strategy', 'res-ncert-geo-mega'],
  progressPercentMap: {
    'ncert-c6-history': 100,
    'ncert-c6-geography': 100,
    'ncert-c11-polity-constitution': 68,
    'hist-s1': 100,
    'pol-s1': 50,
    'geo-s1': 75,
    'eco-s1': 25
  },
  bookmarkedResourceIds: ['res-spectrum-modern', 'res-ncert-economy-ied', 'res-pib-portal'],
  notes: {
    'ncert-c11-polity-constitution': '## Article 32 Writs Summary\n- **Habeas Corpus**: To produce the body (unlawful detention).\n- **Mandamus**: We command (public duty enforcement).\n- **Prohibition**: Higher court to lower court preventing excess jurisdiction.\n- **Certiorari**: Quashing illegal orders.\n- **Quo-Warranto**: By what authority (preventing illegal usurpation of public office).'
  },
  studyStreakDays: 7,
  lastStudyDate: new Date().toISOString().split('T')[0],
  activePlan: undefined,
  profile: DEFAULT_PROFILE,
  timetable: DEFAULT_TIMETABLE,
  studySessions: DEFAULT_SESSIONS
};

export function getLocalProgress(): UserProgressState {
  if (typeof window === 'undefined') return DEFAULT_PROGRESS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PROGRESS;
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_PROGRESS,
      ...parsed,
      profile: parsed.profile || DEFAULT_PROFILE,
      timetable: parsed.timetable || DEFAULT_TIMETABLE,
      studySessions: parsed.studySessions || DEFAULT_SESSIONS
    };
  } catch (e) {
    return DEFAULT_PROGRESS;
  }
}

export function saveLocalProgress(state: Partial<UserProgressState>): UserProgressState {
  if (typeof window === 'undefined') return DEFAULT_PROGRESS;
  try {
    const current = getLocalProgress();
    const updated: UserProgressState = {
      ...current,
      ...state,
      lastStudyDate: new Date().toISOString().split('T')[0]
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

    // Optional background sync with Supabase if active
    if (isSupabaseConfigured && supabase) {
      // Async sync without blocking UI
      syncWithSupabase(updated).catch(console.error);
    }

    return updated;
  } catch (e) {
    return DEFAULT_PROGRESS;
  }
}

async function syncWithSupabase(state: UserProgressState) {
  if (!supabase) return;
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) return;
    const userId = session.user.id;

    // Update profile
    if (state.profile) {
      await supabase.from('profiles').upsert({
        id: userId,
        name: state.profile.name,
        preparation_stage: state.profile.preparationStage,
        target_attempt: state.profile.targetAttemptYear,
        daily_target_hours: state.profile.dailyTargetHours,
        updated_at: new Date().toISOString()
      });
    }

    // Update progress state
    await supabase.from('user_progress').upsert({
      user_id: userId,
      completed_resource_ids: state.completedResourceIds,
      in_progress_resource_ids: state.inProgressResourceIds,
      progress_percent_map: state.progressPercentMap,
      bookmarked_resource_ids: state.bookmarkedResourceIds,
      study_streak_days: state.studyStreakDays,
      last_study_date: state.lastStudyDate,
      updated_at: new Date().toISOString()
    });
  } catch (err) {
    // Non-blocking background sync error
    console.log('Supabase sync status:', err);
  }
}

export function addStudySession(session: StudySession): UserProgressState {
  const current = getLocalProgress();
  const sessions = [session, ...(current.studySessions || [])];
  return saveLocalProgress({ studySessions: sessions });
}

export function updateTimetable(timetable: TimetableEvent[]): UserProgressState {
  return saveLocalProgress({ timetable });
}

export function getStoredResources(): Resource[] {
  if (typeof window === 'undefined') return INITIAL_RESOURCES;
  try {
    const custom = localStorage.getItem(CUSTOM_RESOURCES_KEY);
    if (!custom) return INITIAL_RESOURCES;
    const customParsed: Resource[] = JSON.parse(custom);
    const ids = new Set(customParsed.map(r => r.id));
    return [...customParsed, ...INITIAL_RESOURCES.filter(r => !ids.has(r.id))];
  } catch (e) {
    return INITIAL_RESOURCES;
  }
}

export function saveCustomResource(resource: Resource): Resource[] {
  if (typeof window === 'undefined') return INITIAL_RESOURCES;
  try {
    const existing = getStoredResources();
    const index = existing.findIndex(r => r.id === resource.id);
    let updated: Resource[];
    if (index >= 0) {
      updated = [...existing];
      updated[index] = resource;
    } else {
      updated = [resource, ...existing];
    }
    localStorage.setItem(CUSTOM_RESOURCES_KEY, JSON.stringify(updated));
    return updated;
  } catch (e) {
    return INITIAL_RESOURCES;
  }
}

export function deleteCustomResource(id: string): Resource[] {
  if (typeof window === 'undefined') return INITIAL_RESOURCES;
  try {
    const existing = getStoredResources();
    const updated = existing.filter(r => r.id !== id);
    localStorage.setItem(CUSTOM_RESOURCES_KEY, JSON.stringify(updated));
    return updated;
  } catch (e) {
    return INITIAL_RESOURCES;
  }
}
