import React, { useMemo, useState } from "react";

import type { AnalyticsPoint } from "../types/analytics";


export const ScanTrendChart: React.FC<{ points: AnalyticsPoint[] }> = ({ points }) => {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const chart = useMemo(() => {
    const width = 800;
    const height = 260;
    const padding = 24;
    const max = Math.max(1, ...points.map((point) => point.scans));
    const coordinates = points.map((point, index) => ({
      x: padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2),
      y: height - padding - (point.scans / max) * (height - padding * 2),
    }));
    return { width, height, padding, max, coordinates, line: coordinates.map((point) => `${point.x},${point.y}`).join(" ") };
  }, [points]);

  if (points.length === 0) return <div className="flex h-64 items-center justify-center text-sm text-slate-600">No scan activity in this period</div>;
  const active = activeIndex === null ? null : points[activeIndex];
  const activePoint = activeIndex === null ? null : chart.coordinates[activeIndex];

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${chart.width} ${chart.height}`} role="img" aria-label="QR scan trend" className="h-64 w-full overflow-visible">
        <defs><linearGradient id="scan-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.35" /><stop offset="100%" stopColor="#3B82F6" stopOpacity="0" /></linearGradient></defs>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => <line key={ratio} x1={chart.padding} x2={chart.width - chart.padding} y1={chart.padding + ratio * (chart.height - chart.padding * 2)} y2={chart.padding + ratio * (chart.height - chart.padding * 2)} stroke="rgba(255,255,255,0.06)" />)}
        <polygon points={`${chart.padding},${chart.height - chart.padding} ${chart.line} ${chart.width - chart.padding},${chart.height - chart.padding}`} fill="url(#scan-area)" />
        <polyline points={chart.line} fill="none" stroke="#8B5CF6" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        {chart.coordinates.map((point, index) => (
          <circle key={points[index]?.date} cx={point.x} cy={point.y} r="10" fill="transparent" className="cursor-crosshair" onMouseEnter={() => setActiveIndex(index)} onMouseLeave={() => setActiveIndex(null)} />
        ))}
        {activePoint && <><line x1={activePoint.x} x2={activePoint.x} y1={chart.padding} y2={chart.height - chart.padding} stroke="#A78BFA" strokeDasharray="4 4" /><circle cx={activePoint.x} cy={activePoint.y} r="5" fill="#A78BFA" stroke="#141428" strokeWidth="3" /></>}
      </svg>
      {active && activePoint && <div className="pointer-events-none absolute top-2 rounded-xl border border-white/10 bg-[#0F0F1F] px-3 py-2 text-xs shadow-xl" style={{ left: `${Math.min(82, Math.max(4, activePoint.x / chart.width * 100))}%`, transform: "translateX(-50%)" }}><p className="font-semibold text-white">{active.scans} scans</p><p className="text-slate-500">{active.unique_visitors} unique · {active.date}</p></div>}
      <div className="mt-1 flex justify-between text-[11px] text-slate-700"><span>{points[0]?.date}</span><span>{points.at(-1)?.date}</span></div>
    </div>
  );
};
