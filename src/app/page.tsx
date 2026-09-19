'use client';

import React from 'react';
import Link from 'next/link';
import { 
  ArrowRight, 
  ArrowUpRight, 
  Search, 
  BookOpen, 
  Clock, 
  Layers, 
  ChevronRight, 
  Play, 
  TrendingUp, 
  FileText, 
  ShieldCheck, 
  Sparkles,
  Calendar
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
  const { profile, isAuthenticated } = useAuth();
  const firstName = profile?.name ? profile.name.split(' ')[0] : 'Aspirant';

  const learningLevels = [
    {
      step: '01',
      title: 'NCERT Foundation',
      range: 'Classes 6–10',
      desc: 'Build conceptual fundamentals across History, Geography, Polity, and Science without coaching jargon.',
      href: '/ncert?class=6',
      badge: 'NCERT'
    },
    {
      step: '02',
      title: 'Senior Secondary',
      range: 'Classes 11–12',
      desc: 'High-yield conceptual depth: Indian Constitution at Work, Physical Geography, and Themes in Indian History.',
      href: '/ncert?class=11',
      badge: 'Foundation'
    },
    {
      step: '03',
      title: 'Core UPSC Subjects',
      range: 'Standard Reference',
      desc: 'Structured pathways connecting basic NCERTs with standard reference works and syllabus checkpoints.',
      href: '/roadmaps',
      badge: 'Core Subjects'
    },
    {
      step: '04',
      title: 'Integration & Analysis',
      range: 'Current Affairs & Ethics',
      desc: 'Analytical frameworks linking core static syllabus to PIB releases, PRS summaries, and GS-4 case studies.',
      href: '/current-affairs',
      badge: 'Advanced'
    },
    {
      step: '05',
      title: 'Exam Execution',
      range: 'Prelims + Mains PYQs',
      desc: '15-year past question archives, CSAT problem sets, and structured answer-writing matrices.',
      href: '/pyqs',
      badge: 'Prelims + Mains'
    }
  ];

  const quickSubjects = [
    { name: 'Indian Polity', code: 'GS-2', topics: 'Constitution, Parliament, Judiciary', link: '/roadmaps/polity' },
    { name: 'Modern History', code: 'GS-1', topics: 'British Expansion, Freedom Struggle', link: '/roadmaps/history' },
    { name: 'Physical Geography', code: 'GS-1', topics: 'Geomorphology, Climatology, Mapping', link: '/roadmaps/geography' },
    { name: 'Indian Economy', code: 'GS-3', topics: 'Macroeconomics, Banking, Budget', link: '/roadmaps/economy' },
  ];

  const valuePillars = [
    {
      title: 'Curriculum-first, not algorithm-first',
      desc: 'Resources are organized by academic syllabus and chapter hierarchy, not whatever video happens to trend on YouTube.'
    },
    {
      title: 'Isolated personal workspace',
      desc: 'Your study timer sessions, personal timetable, progress percentages, and private notes are securely isolated to your account.'
    },
    {
      title: '100% Free & Open Infrastructure',
      desc: 'Direct links to verified educators and official NCERT PDFs. Zero commercial paywalls or promotional coaching gimmicks.'
    }
  ];

  return (
    <div className="w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200 select-none">
      {/* ================= COMPACT APPLICATION HERO / HEADER ================= */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/90 shadow-subtle flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-[10px] font-bold tracking-wider text-slate-700 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-900" />
            <span>{isAuthenticated ? `WORKSPACE ACTIVE · ${profile?.preparationStage || 'FOUNDATION'}` : 'OPEN CIVIL SERVICES INFRASTRUCTURE'}</span>
          </div>

          <h1 className="font-display font-extrabold text-2xl sm:text-4xl text-slate-900 tracking-tight leading-tight">
            {isAuthenticated ? (
              <>Good morning, {firstName}. Continue your preparation.</>
            ) : (
              <>Structured learning infrastructure for UPSC preparation.</>
            )}
          </h1>

          <p className="text-xs sm:text-sm text-slate-500 font-sans leading-relaxed">
            {isAuthenticated
              ? 'Resume your active focus session, inspect your daily timetable blocks, and track your chapter mastery.'
              : 'Discover organized academic resources from NCERT Class 6–12 foundations to standard reference roadmaps, focus timers, and PYQ vaults.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 flex-shrink-0">
          {isAuthenticated ? (
            <>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm transition-smooth"
              >
                <span>Open Dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/study"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-800 font-semibold text-xs transition-smooth"
              >
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Focus Timer</span>
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/ncert"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm transition-smooth"
              >
                <span>Explore NCERTs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/auth?mode=signup"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-800 font-semibold text-xs transition-smooth"
              >
                <span>Create Free Account</span>
              </Link>
            </>
          )}
        </div>
      </div>

      {/* ================= CORE SUBJECT LAUNCHPAD ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickSubjects.map((sub, idx) => (
          <Link
            key={idx}
            href={sub.link}
            className="p-4 rounded-xl bg-white border border-slate-200/80 hover:border-slate-300 shadow-subtle hover:shadow-card transition-smooth space-y-2 group"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                {sub.code}
              </span>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-900 transition-colors" />
            </div>
            <div>
              <h3 className="font-display font-bold text-sm text-slate-900 group-hover:text-slate-700">
                {sub.name}
              </h3>
              <p className="text-[11px] text-slate-400 font-sans line-clamp-1">{sub.topics}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* ================= STRUCTURED LEARNING PROGRESSION (FULL WIDTH APP PANEL) ================= */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="space-y-0.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              CURRICULUM HIERARCHY
            </span>
            <h2 className="font-display font-bold text-xl sm:text-2xl text-slate-900 tracking-tight">
              Structured Learning Roadmap
            </h2>
          </div>
          <Link
            href="/roadmaps"
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-900 hover:text-slate-600 transition-colors"
          >
            <span>Explore full syllabus</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 5-Stage Step Nodes Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {learningLevels.map((lvl) => (
            <Link
              key={lvl.step}
              href={lvl.href}
              className="p-4 rounded-xl bg-slate-50/70 hover:bg-slate-100/90 border border-slate-200/70 transition-smooth flex flex-col justify-between space-y-3 group"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-extrabold text-slate-800 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                    {lvl.step}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 font-medium">
                    {lvl.badge}
                  </span>
                </div>
                <h3 className="font-display font-bold text-xs sm:text-sm text-slate-900 group-hover:text-slate-700">
                  {lvl.title}
                </h3>
                <p className="text-[11px] text-slate-500 font-sans line-clamp-2 leading-relaxed">
                  {lvl.desc}
                </p>
              </div>

              <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-700 group-hover:text-slate-900 pt-1 border-t border-slate-200/50">
                <span>View Stage</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* ================= PLATFORM PRINCIPLES ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {valuePillars.map((pillar, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-2"
          >
            <span className="font-mono text-[10px] font-bold text-slate-400">PRINCIPLE 0{idx + 1}</span>
            <h3 className="font-display font-bold text-xs sm:text-sm text-slate-900 leading-snug">
              {pillar.title}
            </h3>
            <p className="text-xs text-slate-500 font-sans leading-relaxed">
              {pillar.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
