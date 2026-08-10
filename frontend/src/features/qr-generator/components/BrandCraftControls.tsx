import React from "react";

import { Button, Input } from "../../../components/ui";
import { cn } from "../../../lib/cn";
import type { QrDesign } from "../types/qrGenerator";

const selectClassName = cn(
  "w-full rounded-xl border border-white/8 bg-white/4 px-4 py-3 text-sm text-slate-200",
  "focus:border-violet-500/60 focus:outline-none focus:ring-2 focus:ring-violet-500/15",
);

const themes = [
  { name: "Violet Sky", start: "#7C3AED", end: "#2563EB" },
  { name: "Ocean", start: "#0F766E", end: "#0284C7" },
  { name: "Sunset", start: "#C2410C", end: "#BE123C" },
  { name: "Midnight", start: "#111827", end: "#4338CA" },
];

interface BrandCraftControlsProps {
  design: QrDesign;
  onChange: <Key extends keyof QrDesign>(key: Key, value: QrDesign[Key]) => void;
  onPreset: (start: string, end: string) => void;
}

export const BrandCraftControls: React.FC<BrandCraftControlsProps> = ({ design, onChange, onPreset }) => (
  <div className="space-y-6 md:col-span-2">
    <div>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div><p className="text-sm font-medium text-slate-300">Gradient themes</p><p className="text-xs text-slate-600">Select a preset or customize the gradient end color.</p></div>
        <Button variant={design.gradient_enabled ? "secondary" : "outline"} size="sm" onClick={() => onChange("gradient_enabled", !design.gradient_enabled)}>{design.gradient_enabled ? "Gradient on" : "Gradient off"}</Button>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {themes.map((theme) => (
          <button key={theme.name} type="button" onClick={() => onPreset(theme.start, theme.end)} className="rounded-xl border border-white/8 p-2 text-left transition-colors hover:border-violet-500/40">
            <span className="block h-7 rounded-lg" style={{ background: `linear-gradient(135deg, ${theme.start}, ${theme.end})` }} />
            <span className="mt-1.5 block text-xs text-slate-400">{theme.name}</span>
          </button>
        ))}
      </div>
      {design.gradient_enabled && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <label className="space-y-1.5 text-sm font-medium text-slate-300">Gradient end color<div className="flex h-11 items-center gap-3 rounded-xl border border-white/8 bg-white/4 px-3"><input type="color" value={design.gradient_color} onChange={(event) => onChange("gradient_color", event.target.value)} className="h-7 w-8 cursor-pointer rounded border-0 bg-transparent" /><span className="font-mono text-xs uppercase text-slate-400">{design.gradient_color}</span></div></label>
          <label className="space-y-1.5 text-sm font-medium text-slate-300">Direction<select value={design.gradient_direction} onChange={(event) => onChange("gradient_direction", event.target.value as QrDesign["gradient_direction"])} className={selectClassName}><option value="diagonal">Diagonal</option><option value="horizontal">Horizontal</option><option value="vertical">Vertical</option></select></label>
        </div>
      )}
    </div>

    <div className="grid gap-5 md:grid-cols-2">
      <div><p className="mb-2 text-sm font-medium text-slate-300">Module pattern</p><div className="grid grid-cols-3 gap-2">{(["square", "rounded", "dots"] as QrDesign["module_style"][]).map((style) => <Button key={style} variant={design.module_style === style ? "secondary" : "outline"} size="sm" onClick={() => onChange("module_style", style)} className="capitalize">{style}</Button>)}</div></div>
      <div><p className="mb-2 text-sm font-medium text-slate-300">Frame</p><div className="grid grid-cols-3 gap-2">{(["none", "square", "rounded"] as QrDesign["frame_style"][]).map((style) => <Button key={style} variant={design.frame_style === style ? "secondary" : "outline"} size="sm" onClick={() => onChange("frame_style", style)} className="capitalize">{style}</Button>)}</div></div>
      {design.frame_style !== "none" && <Input label="Frame text" value={design.frame_text ?? ""} maxLength={40} placeholder="SCAN ME" onChange={(event) => onChange("frame_text", event.target.value || null)} />}
      <label className="space-y-1.5 text-sm font-medium text-slate-300">Error correction<select value={design.error_correction} onChange={(event) => onChange("error_correction", event.target.value as QrDesign["error_correction"])} className={selectClassName}><option value="L">Low (7%)</option><option value="M">Medium (15%)</option><option value="Q">Quartile (25%)</option><option value="H">High (30%)</option></select></label>
      <label className="space-y-1.5 text-sm font-medium text-slate-300">Export size<select value={design.size} onChange={(event) => onChange("size", Number(event.target.value))} className={selectClassName}><option value={512}>512 × 512</option><option value={1024}>1024 × 1024</option><option value={2048}>2048 × 2048</option></select></label>
      <label className="space-y-2 text-sm font-medium text-slate-300">Quiet zone: {design.margin} modules<input type="range" min={0} max={10} value={design.margin} onChange={(event) => onChange("margin", Number(event.target.value))} className="w-full accent-violet-500" /></label>
    </div>
  </div>
);
