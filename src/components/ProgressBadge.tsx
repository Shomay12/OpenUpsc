'use client';

import React from 'react';

interface ProgressBadgeProps {
  itemId: string;
  currentPercent: number; // 0, 25, 50, 75, 100
  onUpdate: (newPercent: number) => void;
  size?: 'sm' | 'md';
}

export default function ProgressBadge({
  itemId,
  currentPercent = 0,
  onUpdate,
  size = 'md'
}: ProgressBadgeProps) {
  const steps = [0, 25, 50, 75, 100];

  return (
    <div className="flex items-center gap-1 bg-slate-100/80 p-0.5 rounded-full border border-slate-200/60">
      {steps.map((val) => {
        const isSelected = currentPercent === val;
        return (
          <button
            key={val}
            type="button"
            onClick={() => onUpdate(val)}
            className={`px-2 py-0.5 text-[10px] font-medium rounded-full transition-smooth ${
              isSelected
                ? val === 100
                  ? 'bg-emerald-600 text-white font-semibold shadow-subtle'
                  : 'bg-slate-900 text-white font-semibold shadow-subtle'
                : 'text-slate-500 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            {val === 0 ? '0%' : val === 100 ? '✓ 100%' : `${val}%`}
          </button>
        );
      })}
    </div>
  );
}
