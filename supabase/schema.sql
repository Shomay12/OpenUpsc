-- =========================================================================
-- UPSC RESOURCE HUB — SUPABASE PRODUCTION RELATIONAL SCHEMA & RLS POLICIES
-- =========================================================================

-- 1. PROFILES TABLE (Linked 1-to-1 with auth.users)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  avatar_url text,
  preparation_stage text default 'Foundation (Class 6-12)',
  target_attempt text default '2028',
  daily_study_target integer default 4,
  preferred_language text default 'Hinglish',
  timezone text default 'Asia/Kolkata',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on profiles
alter table public.profiles enable row level security;

create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can insert own profile"
  on public.profiles for insert
  with check (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

create policy "Users can delete own profile"
  on public.profiles for delete
  using (auth.uid() = id);


-- 2. USER PROGRESS TABLE
create table if not exists public.user_progress (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  resource_id text not null,
  chapter_id text,
  status text default 'in_progress', -- 'not_started', 'in_progress', 'completed'
  progress_percentage integer default 0,
  notes text,
  started_at timestamp with time zone default timezone('utc'::text, now()),
  completed_at timestamp with time zone,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id, resource_id, chapter_id)
);

-- Enable RLS on user_progress
alter table public.user_progress enable row level security;

create policy "Users can view own progress"
  on public.user_progress for select
  using (auth.uid() = user_id);

create policy "Users can insert own progress"
  on public.user_progress for insert
  with check (auth.uid() = user_id);

create policy "Users can update own progress"
  on public.user_progress for update
  using (auth.uid() = user_id);

create policy "Users can delete own progress"
  on public.user_progress for delete
  using (auth.uid() = user_id);


-- 3. STUDY SESSIONS TABLE
create table if not exists public.study_sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  subject text not null,
  topic text,
  resource_id text,
  chapter_id text,
  start_time timestamp with time zone not null,
  end_time timestamp with time zone not null,
  duration_minutes integer not null default 25,
  duration_seconds integer,
  session_type text default 'Focus', -- 'Focus', 'Short Break', 'Long Break'
  completed boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on study_sessions
alter table public.study_sessions enable row level security;

create policy "Users can view own study sessions"
  on public.study_sessions for select
  using (auth.uid() = user_id);

create policy "Users can insert own study sessions"
  on public.study_sessions for insert
  with check (auth.uid() = user_id);

create policy "Users can update own study sessions"
  on public.study_sessions for update
  using (auth.uid() = user_id);

create policy "Users can delete own study sessions"
  on public.study_sessions for delete
  using (auth.uid() = user_id);


-- 4. TIMETABLE EVENTS TABLE
create table if not exists public.timetable_events (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  day_of_week text not null default 'Daily', -- 'Monday'..'Sunday' or 'Daily'
  start_time text not null, -- '06:30'
  end_time text not null,   -- '07:30'
  subject text not null,
  topic text,
  resource_id text,
  resource_title text,
  repeat_rule text default 'daily',
  completed boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on timetable_events
alter table public.timetable_events enable row level security;

create policy "Users can view own timetable events"
  on public.timetable_events for select
  using (auth.uid() = user_id);

create policy "Users can insert own timetable events"
  on public.timetable_events for insert
  with check (auth.uid() = user_id);

create policy "Users can update own timetable events"
  on public.timetable_events for update
  using (auth.uid() = user_id);

create policy "Users can delete own timetable events"
  on public.timetable_events for delete
  using (auth.uid() = user_id);


-- 5. SAVED RESOURCES TABLE
create table if not exists public.saved_resources (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  resource_id text not null,
  resource_title text,
  category text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id, resource_id)
);

-- Enable RLS on saved_resources
alter table public.saved_resources enable row level security;

create policy "Users can view own saved resources"
  on public.saved_resources for select
  using (auth.uid() = user_id);

create policy "Users can insert own saved resources"
  on public.saved_resources for insert
  with check (auth.uid() = user_id);

create policy "Users can delete own saved resources"
  on public.saved_resources for delete
  using (auth.uid() = user_id);


-- 6. USER GOALS TABLE
create table if not exists public.user_goals (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  goal_type text not null, -- 'daily_hours', 'subject_completion', 'mock_test'
  target_value text not null,
  target_date date,
  is_achieved boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on user_goals
alter table public.user_goals enable row level security;

create policy "Users can view own goals"
  on public.user_goals for select
  using (auth.uid() = user_id);

create policy "Users can insert own goals"
  on public.user_goals for insert
  with check (auth.uid() = user_id);

create policy "Users can update own goals"
  on public.user_goals for update
  using (auth.uid() = user_id);

create policy "Users can delete own goals"
  on public.user_goals for delete
  using (auth.uid() = user_id);


-- 7. USER PREFERENCES TABLE
create table if not exists public.user_preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  theme text default 'light',
  preferred_language text default 'Hinglish',
  email_notifications boolean default true,
  daily_reminder_time text default '06:00',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id)
);

-- Enable RLS on user_preferences
alter table public.user_preferences enable row level security;

create policy "Users can view own preferences"
  on public.user_preferences for select
  using (auth.uid() = user_id);

create policy "Users can insert own preferences"
  on public.user_preferences for insert
  with check (auth.uid() = user_id);

create policy "Users can update own preferences"
  on public.user_preferences for update
  using (auth.uid() = user_id);


-- 8. AUTOMATIC PROFILE CREATION TRIGGER ON AUTH SIGNUP
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, avatar_url, preparation_stage, target_attempt, daily_study_target)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    coalesce(new.raw_user_meta_data->>'avatar_url', ''),
    'Foundation (Class 6-12)',
    '2028',
    4
  )
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

-- Trigger definition
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
