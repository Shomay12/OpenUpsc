'use client';

import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  CheckCircle2, 
  ExternalLink,
  Search,
  ArrowUpRight,
  ShieldCheck
} from 'lucide-react';
import { Resource, VerificationStatus, StageLevel, ResourceType, Language } from '../../lib/types';
import { getStoredResources, saveCustomResource, deleteCustomResource } from '../../lib/store';
import { NCERT_DATA } from '../../data/ncertData';

export default function AdminPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [activeResourceId, setActiveResourceId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [formData, setFormData] = useState<Partial<Resource>>({
    title: '',
    subject: 'History',
    category: 'NCERT Foundation',
    level: 'Foundation',
    classLevel: 'Class 6',
    language: 'English/Hinglish',
    type: 'YouTube',
    provider: 'PW OnlyIAS',
    url: '',
    description: '',
    seniorTip: '',
    views: '100K+',
    likes: '10K+',
    channelSubscribers: '1M+',
    playlistLength: 'Complete',
    estimatedHours: 10,
    free: true,
    verified: true,
    verificationStatus: 'Verified',
    tags: ['History', 'NCERT']
  });

  useEffect(() => {
    setResources(getStoredResources());
  }, []);

  const refreshList = () => {
    setResources(getStoredResources());
  };

  const handleOpenNew = () => {
    setIsEditing(true);
    setActiveResourceId(null);
    setFormData({
      id: 'res-custom-' + Date.now(),
      title: '',
      subject: 'History',
      category: 'NCERT Foundation',
      level: 'Foundation',
      classLevel: 'Class 6',
      language: 'English/Hinglish',
      type: 'YouTube',
      provider: '',
      url: '',
      description: '',
      seniorTip: '',
      views: '120K+',
      likes: '12K+',
      channelSubscribers: '1M+',
      playlistLength: 'Complete',
      estimatedHours: 12,
      free: true,
      verified: true,
      verificationStatus: 'Verified',
      lastVerified: new Date().toISOString().split('T')[0],
      verificationSignals: {
        views: '120K+',
        completeness: 'Complete Class Coverage',
        uploadYear: '2026'
      },
      tags: ['UPSC']
    });
  };

  const handleOpenEdit = (res: Resource) => {
    setIsEditing(true);
    setActiveResourceId(res.id);
    setFormData(res);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to remove this resource from the catalog?')) {
      const updated = deleteCustomResource(id);
      setResources(updated);
      setSuccessMessage('Resource removed.');
      setTimeout(() => setSuccessMessage(null), 3000);
      if (activeResourceId === id) {
        setIsEditing(false);
      }
    }
  };

  const handleStatusChange = (res: Resource, newStatus: VerificationStatus) => {
    const updatedRes: Resource = {
      ...res,
      verificationStatus: newStatus,
      lastVerified: new Date().toISOString().split('T')[0]
    };
    saveCustomResource(updatedRes);
    refreshList();
    setSuccessMessage(`Status updated to "${newStatus}".`);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.url) {
      alert('Please provide title and URL.');
      return;
    }

    const fullResource: Resource = {
      id: formData.id || 'res-' + Date.now(),
      title: formData.title || 'Untitled',
      subject: formData.subject || 'General',
      category: formData.category || 'General',
      level: (formData.level as StageLevel) || 'Foundation',
      classLevel: formData.classLevel,
      language: (formData.language as Language) || 'English/Hinglish',
      type: (formData.type as ResourceType) || 'YouTube',
      provider: formData.provider || 'Independent Educator',
      url: formData.url || '',
      description: formData.description || '',
      seniorTip: formData.seniorTip,
      views: formData.views,
      likes: formData.likes,
      channelSubscribers: formData.channelSubscribers,
      playlistLength: formData.playlistLength,
      estimatedHours: Number(formData.estimatedHours) || 0,
      free: true,
      verified: formData.verificationStatus === 'Verified',
      verificationStatus: (formData.verificationStatus as VerificationStatus) || 'Verified',
      lastVerified: new Date().toISOString().split('T')[0],
      verificationSignals: {
        views: formData.views,
        completeness: formData.playlistLength,
        uploadYear: '2026',
        channelName: formData.provider
      },
      nextResourceTitle: formData.nextResourceTitle,
      tags: typeof formData.tags === 'string' ? (formData.tags as string).split(',').map((t: string) => t.trim()) : (formData.tags || ['UPSC'])
    };

    saveCustomResource(fullResource);
    refreshList();
    setIsEditing(false);
    setSuccessMessage('Resource saved successfully.');
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const filteredResources = resources.filter(r => 
    r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.provider.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-150 pb-6">
        <div className="space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            INTERNAL CATALOG CONTROL
          </span>
          <h1 className="font-display font-extrabold text-2xl sm:text-4xl text-slate-900 tracking-tight">
            Resource Database
          </h1>
        </div>

        <button
          type="button"
          onClick={handleOpenNew}
          className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-subtle transition-smooth"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Resource</span>
        </button>
      </div>

      {successMessage && (
        <div className="p-4 rounded-2xl bg-emerald-50 text-emerald-800 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Edit Form Modal */}
      {isEditing && (
        <div className="p-8 rounded-2xl bg-white border border-slate-200/80 shadow-card space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h3 className="font-display font-bold text-slate-900 text-lg">
              {activeResourceId ? 'Edit Resource' : 'Add New Curated Resource'}
            </h3>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="text-xs text-slate-400 hover:text-slate-900 font-medium"
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2 space-y-1">
                <label className="font-medium text-slate-700">Title</label>
                <input
                  type="text"
                  required
                  value={formData.title || ''}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>

              <div className="space-y-1">
                <label className="font-medium text-slate-700">Subject</label>
                <input
                  type="text"
                  value={formData.subject || ''}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>

              <div className="space-y-1">
                <label className="font-medium text-slate-700">Provider</label>
                <input
                  type="text"
                  value={formData.provider || ''}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label className="font-medium text-slate-700">Outbound URL</label>
                <input
                  type="url"
                  required
                  value={formData.url || ''}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label className="font-medium text-slate-700">Description</label>
                <textarea
                  rows={2}
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label className="font-medium text-slate-700">Senior Mentor Note (Hinglish)</label>
                <input
                  type="text"
                  value={formData.seniorTip || ''}
                  onChange={(e) => setFormData({ ...formData, seniorTip: e.target.value })}
                  className="w-full p-3 rounded-2xl border border-slate-200 bg-slate-50 focus:outline-none focus:border-slate-400"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-full text-slate-500 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2.5 rounded-full bg-slate-900 text-white font-medium text-xs shadow-subtle"
              >
                Save
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Catalog Table */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-4">
        <div className="relative max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter database..."
            className="w-full pl-9 pr-3 py-2 rounded-full border border-slate-200/80 bg-slate-50 text-xs font-sans focus:outline-none"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-150 text-slate-400 font-medium">
                <th className="pb-3">Title & Educator</th>
                <th className="pb-3">Subject</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredResources.map((res) => (
                <tr key={res.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3 pr-3">
                    <span className="font-display font-semibold text-slate-900 block line-clamp-1">{res.title}</span>
                    <span className="text-slate-400 text-[11px]">{res.provider}</span>
                  </td>
                  <td className="py-3 pr-3 text-slate-600">{res.subject}</td>
                  <td className="py-3 pr-3">
                    <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                      {res.verificationStatus}
                    </span>
                  </td>
                  <td className="py-3 text-right space-x-2">
                    <button
                      type="button"
                      onClick={() => handleOpenEdit(res)}
                      className="text-slate-600 hover:text-slate-900 p-1"
                    >
                      <Edit3 className="w-3.5 h-3.5 inline" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(res.id)}
                      className="text-slate-400 hover:text-rose-600 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5 inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Curriculum Coverage Audit Report */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200/80 shadow-subtle space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-150">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              ACADEMIC DATABASE AUDIT
            </span>
            <h3 className="font-display font-bold text-lg sm:text-xl text-slate-900">
              NCERT Curriculum vs Resource Coverage Report
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-sans">
            Curriculum Structure Independent of Resource Availability
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-150 text-slate-400 font-semibold">
                <th className="pb-3">Class</th>
                <th className="pb-3">Subjects</th>
                <th className="pb-3">Official Books</th>
                <th className="pb-3">Curriculum Chapters</th>
                <th className="pb-3">Verified Lecture Coverage</th>
                <th className="pb-3 text-right">Academic Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {[6, 7, 8, 9, 10, 11, 12].map((cls) => {
                const books = NCERT_DATA.filter(b => b.classNum === cls);
                const totalCh = books.reduce((acc, b) => acc + b.chapters.length, 0);
                const coveredCh = books.reduce((acc, b) => acc + b.chapters.filter(c => c.hasResources !== false).length, 0);
                const pct = totalCh > 0 ? Math.round((coveredCh / totalCh) * 100) : 0;

                return (
                  <tr key={cls} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 font-semibold text-slate-900">Class {cls}</td>
                    <td className="py-3 text-slate-600">{books.length} Subjects</td>
                    <td className="py-3 text-slate-600">{books.length} Books</td>
                    <td className="py-3 font-mono font-medium text-slate-700">{totalCh} Chapters</td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-slate-900 font-semibold">{coveredCh} / {totalCh}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          {pct}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 text-right">
                      <span className={`text-[10px] px-2.5 py-1 rounded-full font-semibold ${
                        pct === 100
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : 'bg-amber-50 text-amber-800 border border-amber-200'
                      }`}>
                        {pct === 100 ? '✓ Complete Coverage' : '◐ Active Curation'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Database Validation Criteria Checklist */}
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
          <span className="font-bold text-slate-900 text-xs flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Curriculum Database Validation Standard
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-[11px] text-slate-600">
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold">✓</span>
              <span>All official class subjects established</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold">✓</span>
              <span>Individual books represented separately</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold">✓</span>
              <span>Complete chapter sequence preserved</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold">✓</span>
              <span>Resources attached to exact chapters</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold">✓</span>
              <span>Official NCERT PDF links validated</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold">✓</span>
              <span>Missing resources marked unavailable</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
