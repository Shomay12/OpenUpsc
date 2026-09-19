export type Language = 'English' | 'Hinglish' | 'Hindi' | 'English/Hinglish';
export type ResourceType = 'YouTube' | 'PDF' | 'Website' | 'Notes' | 'PYQ';
export type VerificationStatus = 'Verified' | 'Community Popular' | 'Recently Updated' | 'Needs Review' | 'Outdated' | 'Broken Link';
export type ReadingPriority = 'High' | 'Selective' | 'Skim / Basic Only' | 'Must Read';
export type StageLevel = 'Foundation' | 'Standard' | 'Advanced' | 'Prelims' | 'Mains' | 'CSAT' | 'Interview' | 'Integration';
export const NCERT_CLASSES = [6, 7, 8, 9, 10, 11, 12] as const;
export type NCERTClass = typeof NCERT_CLASSES[number];

export interface VerificationSignal {
  views?: string;
  likes?: string;
  subscribers?: string;
  completeness?: string;
  uploadYear?: string;
  channelName?: string;
  qualityNotes?: string;
}

export interface Resource {
  id: string;
  title: string;
  subject: string;
  category: string;
  level: StageLevel;
  classLevel?: string; // e.g. "Class 6", "Class 11", "Standard Reference"
  language: Language;
  type: ResourceType;
  provider: string; // e.g. "PW OnlyIAS", "UPSCprep.com", "UPSC Wallah", "NCERT Official", "PRS India"
  url: string;
  description: string;
  seniorTip?: string; // Hinglish senior aspirant note
  views?: string;
  likes?: string;
  channelSubscribers?: string;
  playlistLength?: string; // e.g. "18 Videos (Complete)"
  estimatedHours: number;
  free: boolean;
  verified: boolean;
  verificationStatus: VerificationStatus;
  lastVerified: string;
  verificationSignals: VerificationSignal;
  prerequisites?: string[];
  nextResourceId?: string;
  nextResourceTitle?: string;
  tags: string[];
}

export type CoverageState = 'FULL' | 'PARTIAL' | 'LIMITED' | 'UNAVAILABLE';
export type UPSCRelevance = 'High' | 'Medium' | 'Supporting';

export interface ChapterResource {
  id: string;
  type: 'Full Lecture' | 'One-Shot' | 'Revision Notes' | 'Official PDF';
  title: string;
  channel?: string;
  url: string;
  language: Language;
  duration?: string;
  verified: boolean;
}

export interface NCERTChapter {
  number: number;
  title: string;
  priority: 'Must Read' | 'Important' | 'Selective' | 'Can Skip';
  upscRelevance?: UPSCRelevance;
  upscRelevanceNote: string;
  keyThemes: string[];
  resources?: ChapterResource[];
  hasResources?: boolean;
}

export interface NCERTBookDetail {
  id: string;
  bookTitle: string;
  chapters: NCERTChapter[];
  officialPdfUrl: string;
}

export interface NCERTSubjectBook {
  id: string;
  classNum: number;
  subjectName: string;
  bookTitle: string;
  books?: NCERTBookDetail[];
  readingPriority: ReadingPriority;
  upscRelevance?: UPSCRelevance;
  estimatedHours: number;
  whyItMatters: string;
  whatToFocusOn: string;
  whatToSkip?: string;
  seniorHinglishAdvice: string;
  officialPdfUrl: string;
  recommendedLectureUrl?: string;
  recommendedLectureTitle?: string;
  recommendedLectureChannel?: string;
  verificationSignal?: string;
  chapters: NCERTChapter[];
  revisionStrategy: string;
  nextStep: string;
  coverageState?: CoverageState;
}

export interface RoadmapStep {
  id: string;
  stepNumber: number;
  title: string;
  level: 'Foundation' | 'Standard' | 'Advanced' | 'Integration';
  tagline: string;
  seniorGuidance: string;
  estimatedTime: string;
  resources: Resource[];
  pyqFocusArea: string;
  actionChecklist: string[];
  nextStepId?: string;
}

export interface SubjectRoadmap {
  subjectId: string;
  subjectName: string;
  iconName: string;
  description: string;
  overviewAdvice: string;
  steps: RoadmapStep[];
}

export interface PYQItem {
  id: string;
  type: 'Prelims' | 'Mains';
  year: number;
  paper: 'GS-1' | 'GS-2' | 'GS-3' | 'GS-4' | 'CSAT' | 'Essay';
  subject: string;
  topic: string;
  question: string;
  options?: string[];
  correctAnswer?: string;
  explanation: string;
  seniorApproachTip: string;
  relatedResourceId?: string;
  relatedSubjectPath?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  preparationStage: 'School / Foundation' | 'Foundation (Class 6-12)' | 'College' | 'College Aspirant' | 'Beginner UPSC aspirant' | 'Beginner UPSC Aspirant' | 'Already preparing' | 'Standard Core' | 'Prelims Focused' | 'Mains Focused' | string;
  targetAttemptYear: string; // e.g. "2027", "2028"
  dailyTargetHours: number; // e.g. 4
  createdAt?: string;
}

export interface StudySession {
  id: string;
  userId?: string;
  subject: string;
  topic: string;
  resourceId?: string;
  resourceTitle?: string;
  startTime: string;
  endTime: string;
  durationMinutes: number;
  sessionType: 'Focus' | 'Short Break' | 'Long Break';
  completed: boolean;
  notes?: string;
  createdAt: string;
}

export interface TimetableEvent {
  id: string;
  userId?: string;
  dayOfWeek: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday' | 'Daily';
  startTime: string; // e.g. "06:30"
  endTime: string;   // e.g. "07:30"
  subject: string;
  topic: string;
  resourceId?: string;
  resourceTitle?: string;
  completed?: boolean;
}

export interface UserProgressState {
  completedResourceIds: string[];
  inProgressResourceIds: string[];
  progressPercentMap: Record<string, number>; // resourceId or subjectId -> 0 | 25 | 50 | 75 | 100
  bookmarkedResourceIds: string[];
  notes: Record<string, string>; // itemId -> markdown note
  studyStreakDays: number;
  lastStudyDate: string;
  activePlan?: UserGeneratedPlan;
  profile?: UserProfile;
  studySessions?: StudySession[];
  timetable?: TimetableEvent[];
}

export interface UserGeneratedPlan {
  currentLevel: string;
  dailyHours: string;
  targetGoal: string;
  generatedDate: string;
  weeklySchedule: {
    weekNumber: number;
    title: string;
    focusSubjects: string[];
    targets: string[];
    estimatedHoursPerWeek: number;
    seniorTip: string;
  }[];
}

