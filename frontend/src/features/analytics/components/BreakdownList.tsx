import React from "react";

import type { AnalyticsBreakdown } from "../types/analytics";


export const BreakdownList: React.FC<{ items: AnalyticsBreakdown[]; emptyLabel?: string }> = ({ items, emptyLabel = "No data yet" }) => (
  <div className="space-y-4">
    {items.length === 0 ? <p className="py-8 text-center text-sm text-slate-600">{emptyLabel}</p> : items.map((item) => (
      <div key={item.label}>
        <div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="truncate capitalize text-slate-400">{item.label}</span><span className="font-medium text-slate-300">{item.value} <span className="text-slate-600">({item.percentage}%)</span></span></div>
        <div className="h-1.5 overflow-hidden rounded-full bg-white/5"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500" style={{ width: `${item.percentage}%` }} /></div>
      </div>
    ))}
  </div>
);
