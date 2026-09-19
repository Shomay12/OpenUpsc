import React from 'react';
import { Sparkles, MessageSquare } from 'lucide-react';

interface SeniorGuidanceBoxProps {
  advice: string;
  title?: string;
  topicTag?: string;
}

export default function SeniorGuidanceBox({
  advice,
  title = 'Mentor Perspective',
  topicTag
}: SeniorGuidanceBoxProps) {
  return (
    <div className="my-5 p-5 sm:p-6 rounded-3xl bg-slate-50/90 border border-slate-200/80 transition-smooth hover:border-slate-300">
      <div className="flex items-start gap-3.5">
        <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center flex-shrink-0 text-xs font-semibold mt-0.5 shadow-subtle">
          ✦
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-900">
              {title}
            </span>
            {topicTag && (
              <span className="text-[10px] font-medium bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded-full">
                {topicTag}
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-700 font-sans leading-relaxed">
            “{advice}”
          </p>
        </div>
      </div>
    </div>
  );
}
