import React, { useEffect, useRef, useState } from "react";
import {
  Camera, CheckCircle2, Clipboard, ExternalLink, FileImage, History,
  ScanLine, ShieldAlert, ShieldCheck, Trash2, Upload, VideoOff, X,
} from "lucide-react";

import { Badge, Button, Card, Spinner } from "../components/ui";
import { useQrScanner, type QrScan } from "../features/qr-scanner";
import { cn } from "../lib/cn";


function riskVariant(scan: QrScan): "success" | "warning" | "danger" | "default" {
  if (!scan.security) return "default";
  if (scan.security.level === "low") return "success";
  if (scan.security.level === "medium") return "warning";
  return "danger";
}

const ScanResultCard: React.FC<{ scan: QrScan; compact?: boolean; onDelete?: () => void }> = ({ scan, compact, onDelete }) => {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(scan.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  return (
    <article className={cn("rounded-2xl border border-white/7 bg-white/[0.025]", compact ? "p-4" : "p-5")}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="purple" className="capitalize">{scan.content_type.replaceAll("_", " ")}</Badge>
            <Badge className="capitalize">{scan.source}</Badge>
            {scan.security && <Badge variant={riskVariant(scan)}>{scan.security.score}/100 risk</Badge>}
          </div>
          <p className="mt-3 break-all text-sm font-medium text-slate-200">{scan.content}</p>
          <p className="mt-1 text-xs text-slate-600">{new Date(scan.created_at).toLocaleString()}</p>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" icon={copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />} onClick={() => void copy()}>
            {copied ? "Copied" : "Copy"}
          </Button>
          {onDelete && <Button aria-label="Delete scan" variant="danger" size="sm" icon={<Trash2 className="h-4 w-4" />} onClick={onDelete} />}
        </div>
      </div>

      {!compact && Object.keys(scan.metadata).length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.entries(scan.metadata).map(([key, value]) => (
            <span key={key} className="rounded-lg bg-white/4 px-2.5 py-1 text-xs text-slate-500">
              <span className="capitalize">{key.replaceAll("_", " ")}</span>: {String(value)}
            </span>
          ))}
        </div>
      )}

      {!compact && scan.security && (
        <div className={cn("mt-4 rounded-xl border p-4", scan.security.is_safe ? "border-emerald-500/20 bg-emerald-500/7" : "border-red-500/20 bg-red-500/7")}>
          <div className="flex items-center gap-2">
            {scan.security.is_safe ? <ShieldCheck className="h-5 w-5 text-emerald-400" /> : <ShieldAlert className="h-5 w-5 text-red-400" />}
            <p className="text-sm font-semibold text-slate-200">
              {scan.security.is_safe ? "No high-risk patterns detected" : "Review this destination before opening"}
            </p>
          </div>
          {[...scan.security.checks, ...scan.security.warnings].map((message) => (
            <p key={message} className="mt-2 text-xs text-slate-500">• {message}</p>
          ))}
          {scan.security.normalized_url && (
            <Button
              className="mt-4"
              variant={scan.security.is_safe ? "secondary" : "danger"}
              size="sm"
              icon={<ExternalLink className="h-4 w-4" />}
              onClick={() => window.open(scan.security?.normalized_url ?? "", "_blank", "noopener,noreferrer")}
            >
              {scan.security.is_safe ? "Open destination" : "Open anyway"}
            </Button>
          )}
        </div>
      )}
    </article>
  );
};


export const QrScannerPage: React.FC = () => {
  const { results, history, total, isScanning, isLoadingHistory, error, scanImage, remove, clearError } = useQrScanner();
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [dragging, setDragging] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraActive(false);
  };

  useEffect(() => () => stopCamera(), []);

  const handleFile = async (file?: File) => {
    if (!file) return;
    clearError();
    await scanImage(file, "upload", file.name).catch(() => undefined);
  };

  const startCamera = async () => {
    setCameraError(null);
    clearError();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraActive(true);
    } catch {
      setCameraError("Camera access was denied or no camera is available.");
      stopCamera();
    }
  };

  const captureCamera = async () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
    if (blob) await scanImage(blob, "webcam", "webcam-capture.jpg").catch(() => undefined);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <section className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2"><Badge variant="success">Local analysis</Badge></div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">SafeScan QR Scanner</h1>
          <p className="mt-1 text-sm text-slate-500">Decode, classify, and inspect QR content before opening it.</p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-white/7 bg-white/3 px-4 py-2">
          <History className="h-4 w-4 text-violet-400" />
          <span className="text-sm text-slate-400">{total} saved scans</span>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card padding="lg">
          <div className="mb-4 flex items-center gap-3"><div className="rounded-xl bg-violet-500/10 p-2.5"><Upload className="h-5 w-5 text-violet-400" /></div><div><h2 className="font-semibold text-white">Upload QR image</h2><p className="text-xs text-slate-600">PNG, JPEG, or WebP up to 10 MB</p></div></div>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => { event.preventDefault(); setDragging(false); void handleFile(event.dataTransfer.files[0]); }}
            className={cn("flex min-h-64 w-full flex-col items-center justify-center rounded-2xl border border-dashed px-6 text-center transition-colors", dragging ? "border-violet-400 bg-violet-500/10" : "border-white/12 bg-white/[0.02] hover:border-violet-500/50 hover:bg-violet-500/5")}
          >
            {isScanning ? <Spinner size="lg" /> : <><FileImage className="h-10 w-10 text-slate-600" /><p className="mt-4 text-sm font-medium text-slate-300">Drop an image here or click to browse</p><p className="mt-1 text-xs text-slate-600">Multiple QR codes in one image are supported</p></>}
          </button>
          <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(event) => { void handleFile(event.target.files?.[0]); event.currentTarget.value = ""; }} />
        </Card>

        <Card padding="lg">
          <div className="mb-4 flex items-center justify-between gap-3"><div className="flex items-center gap-3"><div className="rounded-xl bg-blue-500/10 p-2.5"><Camera className="h-5 w-5 text-blue-400" /></div><div><h2 className="font-semibold text-white">Webcam scanner</h2><p className="text-xs text-slate-600">Point your camera at a QR code</p></div></div>{cameraActive && <Button variant="ghost" size="sm" icon={<X className="h-4 w-4" />} onClick={stopCamera}>Stop</Button>}</div>
          <div className="relative flex min-h-64 overflow-hidden rounded-2xl border border-white/8 bg-black/30">
            <video ref={videoRef} playsInline muted className={cn("h-64 w-full object-cover", !cameraActive && "invisible")} />
            {!cameraActive && <div className="absolute inset-0 flex flex-col items-center justify-center text-center"><VideoOff className="h-10 w-10 text-slate-700" /><p className="mt-3 text-sm text-slate-500">Camera is off</p><Button className="mt-4" size="sm" icon={<Camera className="h-4 w-4" />} onClick={() => void startCamera()}>Start camera</Button></div>}
            {cameraActive && <div className="pointer-events-none absolute inset-1/2 h-36 w-36 -translate-x-1/2 -translate-y-1/2 rounded-2xl border-2 border-violet-400 shadow-[0_0_0_999px_rgba(0,0,0,0.25)]" />}
          </div>
          {cameraError && <p role="alert" className="mt-3 text-xs text-red-400">{cameraError}</p>}
          {cameraActive && <Button fullWidth className="mt-4" loading={isScanning} icon={<ScanLine className="h-4 w-4" />} onClick={() => void captureCamera()}>Scan camera frame</Button>}
        </Card>
      </section>

      {error && <div role="alert" className="flex items-center justify-between gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400"><span>{error.message}</span><button aria-label="Dismiss error" onClick={clearError}><X className="h-4 w-4" /></button></div>}

      {results.length > 0 && <section><div className="mb-3"><h2 className="text-base font-semibold text-white">Latest result{results.length > 1 ? "s" : ""}</h2><p className="text-xs text-slate-600">SafeScan uses local URL heuristics and does not guarantee a destination is malware-free.</p></div><div className="space-y-3">{results.map((scan) => <ScanResultCard key={scan.id} scan={scan} />)}</div></section>}

      <section>
        <div className="mb-3 flex items-center gap-2"><History className="h-4 w-4 text-slate-500" /><h2 className="text-base font-semibold text-white">Scan history</h2></div>
        <Card padding="none" className="overflow-hidden">
          {isLoadingHistory ? <div className="flex min-h-40 items-center justify-center"><Spinner /></div> : history.length === 0 ? <div className="flex min-h-40 flex-col items-center justify-center text-center"><ScanLine className="h-8 w-8 text-slate-700" /><p className="mt-3 text-sm text-slate-500">No scans yet</p></div> : <div className="divide-y divide-white/5 p-3">{history.map((scan) => <ScanResultCard key={scan.id} compact scan={scan} onDelete={() => void remove(scan.id)} />)}</div>}
        </Card>
      </section>
    </div>
  );
};
