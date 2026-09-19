'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Search, 
  BookOpen, 
  Map, 
  CheckSquare, 
  ArrowRight, 
  X, 
  Sparkles,
  Command,
  CornerDownLeft
} from 'lucide-react';
import { getStoredResources } from '../lib/store';
import { Resource } from '../lib/types';

interface SearchCommandProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SearchCommand({ isOpen, onClose }: SearchCommandProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [resources, setResources] = useState<Resource[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setResources(getStoredResources());
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  // Handle keyboard shortcuts (Escape, Enter, Arrow keys)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open handled by parent or window listener
        }
      }
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const quickLinks = [
    { label: 'NCERT Foundation (Class 6–12)', href: '/ncert', icon: BookOpen, tag: 'Foundation' },
    { label: 'Polity Roadmap (Constitution & Laxmikanth)', href: '/roadmaps/polity', icon: Map, tag: 'GS2' },
    { label: 'History Roadmap (Ancient, Modern, Culture)', href: '/roadmaps/history', icon: Map, tag: 'GS1' },
    { label: 'Geography & Mapping Path', href: '/roadmaps/geography', icon: Map, tag: 'GS1' },
    { label: 'Economy (IED, Macro & Banking)', href: '/roadmaps/economy', icon: Map, tag: 'GS3' },
    { label: 'Prelims & Mains PYQ Vault', href: '/pyqs', icon: CheckSquare, tag: 'PYQ' },
  ];

  const filteredResources = query.trim()
    ? resources.filter(r => 
        r.title.toLowerCase().includes(query.toLowerCase()) ||
        r.subject.toLowerCase().includes(query.toLowerCase()) ||
        r.tags.some(t => t.toLowerCase().includes(query.toLowerCase()))
      ).slice(0, 5)
    : [];

  const handleSelect = (href: string) => {
    router.push(href);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-28 px-4 bg-slate-950/40 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-white rounded-3xl shadow-command border border-slate-200/80 overflow-hidden flex flex-col animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-5 py-4 border-b border-slate-150 gap-3">
          <Search className="w-5 h-5 text-slate-400 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search topics, NCERT classes, roadmaps, or standard books..."
            className="w-full text-base font-sans text-slate-900 placeholder:text-slate-400 bg-transparent focus:outline-none"
          />
          {query && (
            <button 
              onClick={() => setQuery('')}
              className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-2 py-1 text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 rounded-md">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-3 space-y-1">
          {query.trim() === '' ? (
            <div className="space-y-1">
              <span className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Suggested Pathways & Quick Links
              </span>
              {quickLinks.map((link, idx) => {
                const Icon = link.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelect(link.href)}
                    className="w-full flex items-center justify-between p-3 rounded-2xl text-left hover:bg-slate-50 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center group-hover:bg-navy-900 group-hover:text-white transition-colors">
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-sm font-medium text-slate-800">{link.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                        {link.tag}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-700 transition-colors" />
                    </div>
                  </button>
                );
              })}
            </div>
          ) : filteredResources.length > 0 ? (
            <div className="space-y-1">
              <span className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Matching Curated Resources
              </span>
              {filteredResources.map((res) => (
                <button
                  key={res.id}
                  type="button"
                  onClick={() => handleSelect(`/resources?search=${encodeURIComponent(res.title)}`)}
                  className="w-full flex items-center justify-between p-3 rounded-2xl text-left hover:bg-slate-50 transition-colors group"
                >
                  <div className="space-y-0.5">
                    <span className="text-sm font-medium text-slate-900 line-clamp-1">{res.title}</span>
                    <p className="text-xs text-slate-500">{res.subject} • {res.provider} • {res.level}</p>
                  </div>
                  <CornerDownLeft className="w-4 h-4 text-slate-300 group-hover:text-navy-900" />
                </button>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-slate-500 space-y-1">
              <p className="font-medium text-slate-700">No matching resources found for "{query}"</p>
              <p>Try searching for "History", "Class 11", "Polity", or "CSAT".</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 px-5 border-t border-slate-100 bg-slate-50/70 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-3">
            <span>Navigation with keyboard</span>
            <span>•</span>
            <span>Press <strong className="text-slate-600">Enter</strong> to open</span>
          </div>
          <button
            onClick={onClose}
            className="hover:text-slate-700 font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
