import React, { useMemo, useRef, useState } from "react";
import {
  AtSign,
  ArrowLeft,
  CheckCircle2,
  Contact,
  Download,
  FileText,
  ImagePlus,
  Link2,
  LockKeyhole,
  Mail,
  MapPin,
  Phone,
  QrCode,
  RotateCcw,
  Save,
  Sparkles,
  Upload,
  Wifi,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Badge, Button, Card, Input } from "../components/ui";
import { BrandedQrPreview } from "../features/qr-generator/components/BrandedQrPreview";
import { BrandCraftControls } from "../features/qr-generator/components/BrandCraftControls";
import { useQrGenerator, type QrAccessMode, type QrDesign, type QrGenerationInput } from "../features/qr-generator";
import { cn } from "../lib/cn";
import { useLocale } from "../features/i18n";


type QrType = "url" | "text" | "email" | "phone" | "wifi" | "contact" | "location";
type DownloadFormat = "png" | "svg" | "pdf";

const qrTypes: { id: QrType; label: string; icon: React.ElementType }[] = [
  { id: "url", label: "URL", icon: Link2 },
  { id: "text", label: "Text", icon: FileText },
  { id: "email", label: "Email", icon: Mail },
  { id: "phone", label: "Phone", icon: Phone },
  { id: "wifi", label: "Wi-Fi", icon: Wifi },
  { id: "contact", label: "Contact", icon: Contact },
  { id: "location", label: "Location", icon: MapPin },
];

const initialFields = {
  url: "",
  text: "",
  email: "",
  subject: "",
  body: "",
  phone: "",
  ssid: "",
  password: "",
  security: "WPA",
  fullName: "",
  organization: "",
  contactPhone: "",
  contactEmail: "",
  latitude: "",
  longitude: "",
  locationName: "",
};

const defaultDesign: QrDesign = {
  foreground_color: "#111827",
  background_color: "#FFFFFF",
  gradient_enabled: false,
  gradient_color: "#7C3AED",
  gradient_direction: "diagonal",
  module_style: "square",
  frame_style: "none",
  frame_text: null,
  error_correction: "H",
  size: 1024,
  margin: 4,
};

const fieldClassName = cn(
  "w-full rounded-xl border border-white/8 bg-white/4 px-4 py-3 text-sm text-slate-200",
  "placeholder:text-slate-600 hover:border-white/12 focus:border-violet-500/60",
  "focus:bg-white/6 focus:outline-none focus:ring-2 focus:ring-violet-500/15",
);


function escapeWifi(value: string): string {
  return value.replace(/([\\;,:\"])/g, "\\$1");
}

function escapeVcard(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/;/g, "\\;").replace(/,/g, "\\,");
}

export const QrGeneratorPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useLocale();
  const { generation, isGenerating, error, generate, download: downloadStored, reset: resetGeneration } = useQrGenerator();
  const [activeType, setActiveType] = useState<QrType>("url");
  const [fields, setFields] = useState(initialFields);
  const [label, setLabel] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [maxScans, setMaxScans] = useState("");
  const [isDynamicUrl, setIsDynamicUrl] = useState(false);
  const [accessMode, setAccessMode] = useState<QrAccessMode>("public");
  const [accessPassword, setAccessPassword] = useState("");
  const [allowedEmails, setAllowedEmails] = useState("");
  const [design, setDesign] = useState<QrDesign>(defaultDesign);
  const [logo, setLogo] = useState<string | null>(null);
  const [downloadFormat, setDownloadFormat] = useState<DownloadFormat | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateField = (name: keyof typeof initialFields, value: string) => {
    resetGeneration();
    setFields((current) => ({ ...current, [name]: value }));
  };

  const updateDesign = <Key extends keyof QrDesign>(key: Key, value: QrDesign[Key]) => {
    setDesign((current) => ({ ...current, [key]: value }));
    resetGeneration();
  };

  const payload = useMemo(() => {
    switch (activeType) {
      case "url":
        return fields.url.trim();
      case "text":
        return fields.text.trim();
      case "email": {
        if (!fields.email.trim()) return "";
        const query = new URLSearchParams();
        if (fields.subject) query.set("subject", fields.subject);
        if (fields.body) query.set("body", fields.body);
        return `mailto:${fields.email.trim()}${query.size ? `?${query}` : ""}`;
      }
      case "phone":
        return fields.phone.trim() ? `tel:${fields.phone.replace(/\s/g, "")}` : "";
      case "wifi":
        return fields.ssid.trim()
          ? `WIFI:T:${fields.security};S:${escapeWifi(fields.ssid)};P:${escapeWifi(fields.password)};H:false;;`
          : "";
      case "contact": {
        if (!fields.fullName.trim()) return "";
        const lines = ["BEGIN:VCARD", "VERSION:3.0", `FN:${escapeVcard(fields.fullName)}`];
        if (fields.organization) lines.push(`ORG:${escapeVcard(fields.organization)}`);
        if (fields.contactPhone) lines.push(`TEL:${escapeVcard(fields.contactPhone)}`);
        if (fields.contactEmail) lines.push(`EMAIL:${escapeVcard(fields.contactEmail)}`);
        return [...lines, "END:VCARD"].join("\r\n");
      }
      case "location":
        return fields.latitude && fields.longitude
          ? `geo:${fields.latitude},${fields.longitude}${
              fields.locationName
                ? `?q=${encodeURIComponent(`${fields.latitude},${fields.longitude}(${fields.locationName})`)}`
                : ""
            }`
          : "";
    }
  }, [activeType, fields]);

  const generationInput = useMemo<QrGenerationInput | null>(() => {
    if (!payload) return null;
    const privateEmails = allowedEmails.split(/[\n,]/).map((value) => value.trim().toLowerCase()).filter(Boolean);
    if (activeType === "url" && accessMode === "password" && accessPassword.length < 8) return null;
    if (activeType === "url" && accessMode === "private" && privateEmails.length === 0) return null;
    const management = {
      ...(label.trim() ? { label: label.trim() } : {}),
      ...(activeType === "url" && isDynamicUrl && expiresAt ? { expires_at: new Date(expiresAt).toISOString() } : {}),
      ...(activeType === "url" && isDynamicUrl && maxScans ? { max_scans: Number(maxScans) } : {}),
      design,
      ...(logo ? { logo_data_url: logo } : {}),
      ...(activeType === "url" ? {
        access_mode: accessMode,
        ...(accessMode === "password" ? { access_password: accessPassword } : {}),
        ...(accessMode === "private" ? { allowed_emails: privateEmails } : {}),
      } : {}),
    };
    switch (activeType) {
      case "url": return { type: "url", url: fields.url.trim(), dynamic: isDynamicUrl, ...management };
      case "text": return { type: "text", text: fields.text.trim(), ...management };
      case "email": return { type: "email", email: fields.email.trim(), subject: fields.subject || undefined, body: fields.body || undefined, ...management };
      case "phone": return { type: "phone", phone: fields.phone.trim(), ...management };
      case "wifi": return { type: "wifi", ssid: fields.ssid.trim(), password: fields.password, security: fields.security as "WPA" | "WEP" | "nopass", ...management };
      case "contact": return { type: "contact", full_name: fields.fullName.trim(), organization: fields.organization || undefined, phone: fields.contactPhone || undefined, email: fields.contactEmail || undefined, ...management };
      case "location": return { type: "location", latitude: Number(fields.latitude), longitude: Number(fields.longitude), name: fields.locationName || undefined, ...management };
    }
  }, [accessMode, accessPassword, activeType, allowedEmails, design, expiresAt, fields, isDynamicUrl, label, logo, maxScans, payload]);

  const previewPayload = generation?.dynamic_url ?? payload;

  const saveGeneration = async () => {
    if (!generationInput) return;
    await generate(generationInput);
  };

  const handleLogo = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !["image/png", "image/jpeg"].includes(file.type) || file.size > 2 * 1024 * 1024) return;
    const reader = new FileReader();
    reader.onload = () => {
      setLogo(typeof reader.result === "string" ? reader.result : null);
      setDesign((current) => ({ ...current, error_correction: "H" }));
      resetGeneration();
    };
    reader.readAsDataURL(file);
  };

  const download = async (format: DownloadFormat) => {
    if (!generation) return;
    setDownloadFormat(format);
    try {
      await downloadStored(format);
    } finally {
      setDownloadFormat(null);
    }
  };

  const resetStyle = () => {
    setDesign(defaultDesign);
    setLogo(null);
    resetGeneration();
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Badge variant="purple">{t("generator.badge")}</Badge>
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> {t("generator.live")}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">{t("generator.title")}</h1>
          <p className="mt-1 text-sm text-slate-500">{t("generator.description")}</p>
        </div>
        <Button
          variant="outline"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </Button>
      </div>

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
        <div className="space-y-6">
          <Card padding="none" className="overflow-visible">
            <div className="border-b border-white/6 p-5">
              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">{t("generator.type")}</p>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {qrTypes.map(({ id, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => { setActiveType(id); resetGeneration(); }}
                    className={cn(
                      "flex min-w-fit items-center gap-2 rounded-xl border px-3.5 py-2.5 text-sm transition-all",
                      activeType === id
                        ? "border-violet-500/40 bg-violet-500/12 text-violet-300 shadow-[0_0_20px_rgba(124,58,237,0.12)]"
                        : "border-white/6 bg-white/2 text-slate-500 hover:border-white/12 hover:text-slate-300",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {t(`generator.${id}`)}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-5 p-6">
              {activeType === "url" && (
                <div className="space-y-5">
                  <Input label={t("generator.destination")} type="url" value={fields.url} onChange={(event) => updateField("url", event.target.value)} placeholder="https://" icon={<Link2 className="h-4 w-4" />} />
                  <div>
                    <p className="mb-2 text-sm font-medium text-slate-300">URL behavior</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <button
                        type="button"
                        onClick={() => { setIsDynamicUrl(false); setAccessMode("public"); resetGeneration(); }}
                        className={cn(
                          "rounded-xl border p-3 text-left transition-colors",
                          !isDynamicUrl ? "border-emerald-500/35 bg-emerald-500/8" : "border-white/7 bg-white/2 hover:border-white/12",
                        )}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className={cn("text-sm font-semibold", !isDynamicUrl ? "text-emerald-300" : "text-slate-300")}>Direct URL</span>
                          <Badge variant="success">Recommended</Badge>
                        </div>
                        <p className="mt-1 text-xs leading-relaxed text-slate-600">The QR contains your exact website URL and works without IntelliQR running.</p>
                      </button>
                      <button
                        type="button"
                        onClick={() => { setIsDynamicUrl(true); resetGeneration(); }}
                        className={cn(
                          "rounded-xl border p-3 text-left transition-colors",
                          isDynamicUrl ? "border-violet-500/40 bg-violet-500/10" : "border-white/7 bg-white/2 hover:border-white/12",
                        )}
                      >
                        <span className={cn("text-sm font-semibold", isDynamicUrl ? "text-violet-300" : "text-slate-300")}>Dynamic & tracked</span>
                        <p className="mt-1 text-xs leading-relaxed text-slate-600">Uses an IntelliQR redirect for analytics, editing, limits, and protection.</p>
                      </button>
                    </div>
                  </div>
                </div>
              )}
              {activeType === "text" && (
                <label className="block space-y-1.5 text-sm font-medium text-slate-300">
                  Text content
                  <textarea value={fields.text} onChange={(event) => updateField("text", event.target.value)} rows={6} maxLength={4000} placeholder={t("generator.textPlaceholder")} className={fieldClassName} />
                </label>
              )}
              {activeType === "email" && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input label="Email address" type="email" value={fields.email} onChange={(event) => updateField("email", event.target.value)} icon={<AtSign className="h-4 w-4" />} />
                  <Input label="Subject" value={fields.subject} onChange={(event) => updateField("subject", event.target.value)} />
                  <label className="space-y-1.5 text-sm font-medium text-slate-300 sm:col-span-2">
                    Message
                    <textarea value={fields.body} onChange={(event) => updateField("body", event.target.value)} rows={4} className={fieldClassName} />
                  </label>
                </div>
              )}
              {activeType === "phone" && (
                <Input label="Phone number" type="tel" value={fields.phone} onChange={(event) => updateField("phone", event.target.value)} placeholder="+91" icon={<Phone className="h-4 w-4" />} />
              )}
              {activeType === "wifi" && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input label="Network name" value={fields.ssid} onChange={(event) => updateField("ssid", event.target.value)} icon={<Wifi className="h-4 w-4" />} />
                  <label className="space-y-1.5 text-sm font-medium text-slate-300">
                    Security
                    <select value={fields.security} onChange={(event) => updateField("security", event.target.value)} className={fieldClassName}>
                      <option value="WPA">WPA/WPA2</option>
                      <option value="WEP">WEP</option>
                      <option value="nopass">No password</option>
                    </select>
                  </label>
                  <div className="sm:col-span-2">
                    <Input label="Password" type="password" value={fields.password} onChange={(event) => updateField("password", event.target.value)} />
                  </div>
                </div>
              )}
              {activeType === "contact" && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input label="Full name" value={fields.fullName} onChange={(event) => updateField("fullName", event.target.value)} icon={<Contact className="h-4 w-4" />} />
                  <Input label="Organization" value={fields.organization} onChange={(event) => updateField("organization", event.target.value)} />
                  <Input label="Phone" type="tel" value={fields.contactPhone} onChange={(event) => updateField("contactPhone", event.target.value)} />
                  <Input label="Email" type="email" value={fields.contactEmail} onChange={(event) => updateField("contactEmail", event.target.value)} />
                </div>
              )}
              {activeType === "location" && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input label="Latitude" type="number" step="any" value={fields.latitude} onChange={(event) => updateField("latitude", event.target.value)} />
                  <Input label="Longitude" type="number" step="any" value={fields.longitude} onChange={(event) => updateField("longitude", event.target.value)} />
                  <div className="sm:col-span-2">
                    <Input label="Location name" value={fields.locationName} onChange={(event) => updateField("locationName", event.target.value)} icon={<MapPin className="h-4 w-4" />} />
                  </div>
                </div>
              )}
            </div>
          </Card>

          {activeType === "url" && isDynamicUrl && (
            <Card padding="md">
              <div className="mb-5 flex items-start gap-3">
                <div className="rounded-xl bg-violet-500/10 p-2.5"><LockKeyhole className="h-5 w-5 text-violet-400" /></div>
                <div><div className="flex items-center gap-2"><h2 className="font-semibold text-white">SecureVault™ Protection</h2>{accessMode !== "public" && <Badge variant="purple">AES encrypted</Badge>}</div><p className="text-xs text-slate-600">Control who can open this dynamic destination.</p></div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {([
                  ["public", "Public", "Open immediately"],
                  ["password", "Password", "Shared password required"],
                  ["authenticated", "Members", "Any signed-in user"],
                  ["private", "Private", "Allowed accounts only"],
                ] as const).map(([mode, title, description]) => (
                  <button key={mode} type="button" onClick={() => { setAccessMode(mode); resetGeneration(); }} className={cn("rounded-xl border p-3 text-left transition-colors", accessMode === mode ? "border-violet-500/40 bg-violet-500/10" : "border-white/7 bg-white/2 hover:border-white/12")}><p className={cn("text-sm font-medium", accessMode === mode ? "text-violet-300" : "text-slate-300")}>{title}</p><p className="mt-0.5 text-xs text-slate-600">{description}</p></button>
                ))}
              </div>
              {accessMode === "password" && <div className="mt-4"><Input label="Access password" type="password" minLength={8} maxLength={72} value={accessPassword} onChange={(event) => { setAccessPassword(event.target.value); resetGeneration(); }} placeholder="At least 8 characters" icon={<LockKeyhole className="h-4 w-4" />} /><p className="mt-1.5 text-xs text-slate-700">Only a bcrypt hash is stored. The original password cannot be recovered.</p></div>}
              {accessMode === "private" && <div className="mt-4"><label className="block space-y-1.5 text-sm font-medium text-slate-300">Allowed email addresses<textarea rows={3} value={allowedEmails} onChange={(event) => { setAllowedEmails(event.target.value); resetGeneration(); }} placeholder="member@example.com, client@example.com" className={fieldClassName} /></label><p className="mt-1.5 text-xs text-slate-700">Up to 25 registered IntelliQR accounts, separated by commas or new lines.</p></div>}
              {accessMode !== "public" && <p className="mt-4 rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-3 text-xs leading-relaxed text-emerald-300/80">The destination is encrypted with AES-256-GCM. Scanning opens a local access screen and produces a short-lived, QR-specific JWT grant only after authorization.</p>}
            </Card>
          )}

          <Card padding="md">
            <div className="mb-5">
              <h2 className="font-semibold text-white">QR management</h2>
              <p className="text-xs text-slate-600">
                Name this QR code. URL QR codes also support dynamic redirect controls.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Input
                  label="Label"
                  value={label}
                  maxLength={80}
                  placeholder="Example: Product website"
                  onChange={(event) => { setLabel(event.target.value); resetGeneration(); }}
                />
              </div>
              {activeType === "url" && isDynamicUrl && (
                <>
                  <Input
                    label="Expiry date (optional)"
                    type="datetime-local"
                    value={expiresAt}
                    min={new Date().toISOString().slice(0, 16)}
                    onChange={(event) => { setExpiresAt(event.target.value); resetGeneration(); }}
                  />
                  <Input
                    label="Maximum scans (optional)"
                    type="number"
                    min={1}
                    max={10000000}
                    value={maxScans}
                    placeholder="Unlimited"
                    onChange={(event) => { setMaxScans(event.target.value); resetGeneration(); }}
                  />
                  <p className="text-xs leading-relaxed text-slate-600 sm:col-span-2">
                    The generated QR points to a stable local link. You can change its destination, pause it, or update these limits later from Dashboard without regenerating the image.
                  </p>
                </>
              )}
              {activeType === "url" && !isDynamicUrl && (
                <p className="text-xs leading-relaxed text-slate-600 sm:col-span-2">
                  Direct URL mode stores the exact website address in the QR. Scan analytics, destination editing, expiry, limits, and SecureVault require Dynamic & tracked mode.
                </p>
              )}
            </div>
          </Card>

          <Card padding="md">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-white">BrandCraft™ Studio</h2>
                <p className="text-xs text-slate-600">Design settings are persisted and rendered by the backend.</p>
              </div>
              <Button variant="ghost" size="sm" icon={<RotateCcw className="h-3.5 w-3.5" />} onClick={resetStyle}>Reset</Button>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              {[
                { label: "Foreground", key: "foreground_color" as const, value: design.foreground_color },
                { label: "Background", key: "background_color" as const, value: design.background_color },
              ].map(({ label: colorLabel, key, value }) => (
                <label key={key} className="space-y-2 text-sm font-medium text-slate-300">
                  {colorLabel}
                  <div className="flex h-11 items-center gap-3 rounded-xl border border-white/8 bg-white/4 px-3">
                    <input type="color" value={value} onChange={(event) => updateDesign(key, event.target.value)} className="h-7 w-8 cursor-pointer rounded border-0 bg-transparent" />
                    <span className="font-mono text-xs uppercase text-slate-400">{value}</span>
                  </div>
                </label>
              ))}

              <BrandCraftControls
                design={design}
                onChange={updateDesign}
                onPreset={(start, end) => {
                  setDesign((current) => ({ ...current, foreground_color: start, gradient_color: end, gradient_enabled: true }));
                  resetGeneration();
                }}
              />

              <div className="md:col-span-2">
                <p className="mb-2 text-sm font-medium text-slate-300">Logo</p>
                <input ref={fileInputRef} type="file" accept="image/png,image/jpeg" onChange={handleLogo} className="hidden" />
                {logo ? (
                  <div className="flex items-center justify-between rounded-xl border border-violet-500/25 bg-violet-500/8 p-3">
                    <div className="flex items-center gap-3">
                      <img src={logo} alt="Uploaded QR logo" className="h-10 w-10 rounded-lg bg-white object-contain p-1" />
                      <div>
                        <p className="text-sm font-medium text-slate-200">Logo added</p>
                        <p className="text-xs text-slate-600">Centered with an excavated background</p>
                      </div>
                    </div>
                    <button type="button" onClick={() => { setLogo(null); resetGeneration(); }} className="rounded-lg p-2 text-slate-500 hover:bg-white/5 hover:text-white" aria-label="Remove logo">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <button type="button" onClick={() => fileInputRef.current?.click()} className="flex w-full items-center justify-center gap-3 rounded-xl border border-dashed border-white/12 bg-white/2 px-4 py-6 text-sm text-slate-500 transition-colors hover:border-violet-500/40 hover:bg-violet-500/5 hover:text-violet-300">
                    <Upload className="h-4 w-4" /> Upload PNG or JPG · Max 2 MB
                  </button>
                )}
              </div>
            </div>
          </Card>
        </div>

        <aside className="min-w-0 self-start">
          <Card padding="none" glow className="overflow-hidden border-violet-500/20">
            <div className="flex items-center justify-between border-b border-white/6 px-5 py-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold text-white">{t("generator.live")}</h2>
                  <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-400">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" /> Live
                  </span>
                </div>
                <p className="text-xs text-slate-600">{t("generator.liveDesc")}</p>
              </div>
              <div className="rounded-xl border border-violet-500/20 bg-violet-500/10 p-2.5">
                <Sparkles className="h-4 w-4 text-violet-300" />
              </div>
            </div>

            <div className="p-4 sm:p-5">
              <div className="relative flex min-h-[310px] w-full items-center justify-center overflow-hidden rounded-[1.75rem] border border-white/8 bg-[#090914] p-5 sm:min-h-[340px] sm:p-6">
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_5%,rgba(124,58,237,0.22),transparent_48%)]" />
                <div className="pointer-events-none absolute inset-3 rounded-[1.35rem] border border-white/[0.035]" />
                <div className="pointer-events-none absolute -left-16 bottom-0 h-40 w-40 rounded-full bg-blue-500/5 blur-3xl" />
                {previewPayload ? (
                  <div className="relative aspect-square w-full max-w-[270px] overflow-hidden rounded-[1.5rem] bg-white p-4 shadow-[0_26px_90px_rgba(0,0,0,0.55),0_0_0_1px_rgba(255,255,255,0.08)]">
                    <BrandedQrPreview
                      value={previewPayload}
                      design={design}
                      logo={logo}
                      className="block h-full w-full"
                    />
                  </div>
                ) : (
                  <div className="relative flex max-w-xs flex-col items-center px-5 text-center">
                    <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-3xl border border-violet-500/20 bg-violet-500/8 shadow-[0_0_45px_rgba(124,58,237,0.12)]">
                      <ImagePlus className="h-8 w-8 text-violet-300/60" />
                    </div>
                    <p className="font-semibold text-slate-200">Your QR preview will appear here</p>
                    <p className="mt-2 text-xs leading-relaxed text-slate-600">Enter the required {activeType} content. Design changes will update this preview instantly.</p>
                  </div>
                )}
              </div>

              <div className="mt-4" aria-live="polite">
                <Button
                  id="generator-save"
                  variant={generation ? "secondary" : "primary"}
                  size="lg"
                  fullWidth
                  icon={generation ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <Save className="h-5 w-5" />}
                  iconRight={!generation && !isGenerating ? <Sparkles className="h-4 w-4" /> : undefined}
                  loading={isGenerating}
                  disabled={!generationInput || Boolean(generation)}
                  onClick={() => void saveGeneration()}
                  className={cn(
                    "h-14 rounded-2xl text-base",
                    generation && "border-emerald-500/25 bg-emerald-500/8 text-emerald-300",
                  )}
                >
                  {generation ? "QR saved to Dashboard" : "Save QR to Dashboard"}
                </Button>
                {!generationInput && (
                  <p className="mt-2 text-center text-[11px] text-slate-600">
                    Complete the required content to enable saving.
                  </p>
                )}
              </div>

              {error && (
                <p role="alert" className="mt-3 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-400">
                  {error.message}
                </p>
              )}

              {generation && (
                <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/8 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant="success">{t("generator.saved")}</Badge>
                    <span className="text-xs capitalize text-slate-500">{generation.status}</span>
                  </div>
                  {generation.dynamic_url && (
                    <p className="mt-2 break-all font-mono text-[11px] text-slate-500">{generation.dynamic_url}</p>
                  )}
                </div>
              )}

              <div className="mt-5 border-t border-white/6 pt-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">{t("generator.download")}</p>
                  <span className="text-[11px] text-slate-700">PNG, SVG or PDF</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {(["png", "svg", "pdf"] as DownloadFormat[]).map((format) => (
                    <Button
                      key={format}
                      variant={generation && format === "png" ? "primary" : "outline"}
                      size="sm"
                      icon={<Download className="h-3.5 w-3.5" />}
                      loading={downloadFormat === format}
                      disabled={!generation}
                      onClick={() => void download(format)}
                    >
                      {format.toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
};
