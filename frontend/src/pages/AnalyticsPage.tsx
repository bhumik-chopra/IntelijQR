import React, { useState } from "react";
import {
  Activity, BarChart3, CalendarDays, Globe2, MonitorSmartphone,
  QrCode, RefreshCw, TrendingDown, TrendingUp, Users,
} from "lucide-react";

import { Badge, Button, Card, Spinner } from "../components/ui";
import { BreakdownList, ScanTrendChart, useAnalytics, type AnalyticsPeriod } from "../features/analytics";
import { useQrGenerations } from "../features/qr-generator";


const periods: { value: AnalyticsPeriod; label: string }[] = [
  { value: "7d", label: "7 days" }, { value: "30d", label: "30 days" },
  { value: "90d", label: "90 days" }, { value: "12m", label: "12 months" },
];


export const AnalyticsPage: React.FC = () => {
  const [period, setPeriod] = useState<AnalyticsPeriod>("30d");
  const [qrId, setQrId] = useState("");
  const { data, isLoading, error, reload } = useAnalytics(period, qrId || undefined);
  const { items: qrCodes } = useQrGenerations({ limit: 100, type: "url" });
  const average = data ? data.total_scans / (period === "7d" ? 7 : period === "30d" ? 30 : period === "90d" ? 90 : 365) : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div><div className="mb-2 flex items-center gap-2"><Badge variant="success">Live data</Badge></div><h1 className="text-2xl font-bold text-white sm:text-3xl">Smart QR Analytics</h1><p className="mt-1 text-sm text-slate-500">Understand how your dynamic QR codes perform across visitors and devices.</p></div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <select aria-label="Filter analytics by QR code" value={qrId} onChange={(event) => setQrId(event.target.value)} className="h-10 min-w-52 rounded-xl border border-white/10 bg-[#141428] px-3 text-sm text-slate-300 focus:border-violet-500/60 focus:outline-none"><option value="">All dynamic QR codes</option>{qrCodes.map((qr) => <option key={qr.id} value={qr.id}>{qr.label || qr.payload_preview}</option>)}</select>
          <div className="flex rounded-xl border border-white/8 bg-white/3 p-1">{periods.map((item) => <button key={item.value} onClick={() => setPeriod(item.value)} className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${period === item.value ? "bg-violet-500/20 text-violet-300" : "text-slate-600 hover:text-slate-300"}`}>{item.label}</button>)}</div>
        </div>
      </section>

      {error && <div role="alert" className="flex items-center justify-between rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400"><span>{error.message}</span><Button variant="ghost" size="sm" icon={<RefreshCw className="h-4 w-4" />} onClick={() => void reload()}>Retry</Button></div>}

      {isLoading && !data ? <Card className="flex min-h-80 items-center justify-center"><Spinner size="lg" /></Card> : data && <>
        <section aria-label="Analytics summary" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card padding="md"><div className="flex items-start justify-between"><div><p className="text-xs text-slate-600">Total scans</p><p className="mt-2 text-3xl font-bold text-white">{data.total_scans.toLocaleString()}</p>{data.scan_change_percentage === null ? <p className="mt-2 text-xs text-slate-600">No previous-period baseline</p> : <p className={`mt-2 flex items-center gap-1 text-xs ${data.scan_change_percentage >= 0 ? "text-emerald-400" : "text-red-400"}`}>{data.scan_change_percentage >= 0 ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}{Math.abs(data.scan_change_percentage)}% vs previous period</p>}</div><Activity className="h-5 w-5 text-violet-400" /></div></Card>
          <Card padding="md"><div className="flex items-start justify-between"><div><p className="text-xs text-slate-600">Unique visitors</p><p className="mt-2 text-3xl font-bold text-white">{data.unique_visitors.toLocaleString()}</p><p className="mt-2 text-xs text-slate-600">Privacy-safe fingerprint estimate</p></div><Users className="h-5 w-5 text-blue-400" /></div></Card>
          <Card padding="md"><div className="flex items-start justify-between"><div><p className="text-xs text-slate-600">Average per day</p><p className="mt-2 text-3xl font-bold text-white">{average.toFixed(1)}</p><p className="mt-2 text-xs text-slate-600">During selected period</p></div><CalendarDays className="h-5 w-5 text-emerald-400" /></div></Card>
          <Card padding="md"><div className="flex items-start justify-between"><div><p className="text-xs text-slate-600">Top QR code</p><p className="mt-2 max-w-44 truncate text-lg font-bold text-white">{data.top_qr_codes[0]?.label ?? "No activity"}</p><p className="mt-2 text-xs text-slate-600">{data.top_qr_codes[0]?.scans ?? 0} scans</p></div><QrCode className="h-5 w-5 text-amber-400" /></div></Card>
        </section>

        <Card padding="lg"><div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold text-white">Scan activity</h2><p className="text-xs text-slate-600">Scans and unique visitors over time</p></div><BarChart3 className="h-5 w-5 text-violet-400" /></div><ScanTrendChart points={data.series} /></Card>

        <section className="grid gap-4 lg:grid-cols-3">
          <Card padding="md"><div className="mb-5 flex items-center gap-2"><MonitorSmartphone className="h-4 w-4 text-violet-400" /><h2 className="text-sm font-semibold text-white">Devices</h2></div><BreakdownList items={data.devices} /></Card>
          <Card padding="md"><div className="mb-5 flex items-center gap-2"><Globe2 className="h-4 w-4 text-blue-400" /><h2 className="text-sm font-semibold text-white">Browsers</h2></div><BreakdownList items={data.browsers} /></Card>
          <Card padding="md"><div className="mb-5 flex items-center gap-2"><Activity className="h-4 w-4 text-emerald-400" /><h2 className="text-sm font-semibold text-white">Operating systems</h2></div><BreakdownList items={data.operating_systems} /></Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <Card padding="md"><div className="mb-5 flex items-center gap-2"><Globe2 className="h-4 w-4 text-blue-400" /><div><h2 className="text-sm font-semibold text-white">Location</h2><p className="text-xs text-slate-600">Country and city from local network context</p></div></div><div className="grid gap-6 sm:grid-cols-2"><div><p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-700">Countries</p><BreakdownList items={data.countries} /></div><div><p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-700">Cities</p><BreakdownList items={data.cities} /></div></div></Card>
          <Card padding="md"><div className="mb-5 flex items-center gap-2"><QrCode className="h-4 w-4 text-violet-400" /><h2 className="text-sm font-semibold text-white">Top performing QR codes</h2></div>{data.top_qr_codes.length === 0 ? <p className="py-8 text-center text-sm text-slate-600">No scan activity yet</p> : <div className="space-y-3">{data.top_qr_codes.map((qr, index) => <div key={qr.id} className="flex items-center gap-3 rounded-xl bg-white/3 p-3"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-xs font-bold text-violet-400">{index + 1}</span><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-slate-300">{qr.label}</p><p className="text-xs text-slate-600">{qr.unique_visitors} unique visitors</p></div><span className="text-sm font-semibold text-white">{qr.scans}</span></div>)}</div>}</Card>
        </section>

        <Card padding="none"><div className="border-b border-white/6 p-5"><h2 className="font-semibold text-white">Recent scan events</h2><p className="text-xs text-slate-600">The latest dynamic QR redirects in this period</p></div>{data.recent_scans.length === 0 ? <p className="p-10 text-center text-sm text-slate-600">Scan a dynamic QR code to begin collecting analytics.</p> : <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-white/6 text-xs uppercase tracking-wider text-slate-700"><tr><th className="px-5 py-3">QR code</th><th className="px-5 py-3">Device</th><th className="px-5 py-3">Browser / OS</th><th className="px-5 py-3">Location</th><th className="px-5 py-3">Time</th></tr></thead><tbody className="divide-y divide-white/5">{data.recent_scans.map((scan) => <tr key={scan.id}><td className="max-w-60 truncate px-5 py-4 font-medium text-slate-300">{scan.qr_label}</td><td className="px-5 py-4 capitalize text-slate-500">{scan.device_type}</td><td className="px-5 py-4 text-slate-500">{scan.browser} · {scan.operating_system}</td><td className="px-5 py-4 text-slate-500">{scan.city}, {scan.country}</td><td className="whitespace-nowrap px-5 py-4 text-slate-600">{new Date(scan.scanned_at).toLocaleString()}</td></tr>)}</tbody></table></div>}</Card>

        <p className="text-xs text-slate-700">Detailed analytics begin with recorded scans. Raw IP addresses and complete user-agent strings are not stored. Public geolocation requires a local GeoIP database and currently appears as Unknown.</p>
      </>}
    </div>
  );
};
