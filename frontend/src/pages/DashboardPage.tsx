import React, { useDeferredValue, useState } from "react";
import {
  ArrowRight,
  Check,
  Clock3,
  Download,
  Pause,
  Pencil,
  Play,
  QrCode,
  ScanLine,
  BarChart3,
  Layers3,
  Share2,
  Search,
  Activity,
  FileLock2,
  Star,
  Trash2,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Avatar, Badge, Button, Card, Input, Spinner } from "../components/ui";
import { useAuth } from "../features/auth";
import { useDashboardSummary } from "../features/personal-dashboard";
import { useLocale } from "../features/i18n";
import {
  qrGeneratorApi,
  useQrGenerations,
  type QrDownloadFormat,
  type QrGeneration,
  type QrPayloadType,
  type QrStatus,
} from "../features/qr-generator";

const downloadFormats: QrDownloadFormat[] = ["png", "svg", "pdf"];

interface EditForm {
  label: string;
  destinationUrl: string;
  expiresAt: string;
  maxScans: string;
}

function toLocalDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function statusVariant(status: QrStatus): "success" | "warning" | "danger" | "default" {
  if (status === "active") return "success";
  if (status === "paused") return "warning";
  if (status === "expired" || status === "scan_limit_reached") return "danger";
  return "default";
}

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useLocale();
  const { data: summary, isLoading: isSummaryLoading, error: summaryError } = useDashboardSummary();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [typeFilter, setTypeFilter] = useState<QrPayloadType | "">("");
  const [statusFilter, setStatusFilter] = useState<QrStatus | "">("");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({ label: "", destinationUrl: "", expiresAt: "", maxScans: "" });
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { items, total, isLoading, error, reload } = useQrGenerations({
    limit: 100,
    search: deferredSearch,
    type: typeFilter || undefined,
    status: statusFilter || undefined,
    favorite: favoritesOnly ? true : undefined,
  });

  const runAction = async (id: string, action: () => Promise<unknown>) => {
    setActionId(id);
    setActionError(null);
    try {
      await action();
      await reload();
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "QR update failed");
    } finally {
      setActionId(null);
    }
  };

  const startEditing = (item: QrGeneration) => {
    setDeleteId(null);
    setEditingId(item.id);
    setEditForm({
      label: item.label ?? "",
      destinationUrl: item.destination_url ?? "",
      expiresAt: toLocalDateTime(item.expires_at),
      maxScans: item.max_scans?.toString() ?? "",
    });
  };

  const saveEdit = (item: QrGeneration) => runAction(item.id, async () => {
    await qrGeneratorApi.update(item.id, {
      label: editForm.label.trim() || null,
      ...(item.dynamic_url ? {
        destination_url: editForm.destinationUrl.trim(),
        expires_at: editForm.expiresAt ? new Date(editForm.expiresAt).toISOString() : null,
        max_scans: editForm.maxScans ? Number(editForm.maxScans) : null,
      } : {}),
    });
    setEditingId(null);
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Avatar name={user?.name ?? "User"} size="lg" />
          <div>
            <p className="text-sm text-slate-600">{t("dashboard.welcome")}</p>
            <h1 className="text-2xl font-bold text-white">{user?.name ?? "IntelliQR user"}</h1>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" icon={<Share2 className="h-4 w-4" />} onClick={() => navigate("/share-vault")}>
            {t("nav.share")}
          </Button>
          <Button variant="outline" icon={<Layers3 className="h-4 w-4" />} onClick={() => navigate("/bulk")}>
            {t("nav.bulk")}
          </Button>
          <Button variant="outline" icon={<BarChart3 className="h-4 w-4" />} onClick={() => navigate("/analytics")}>
            {t("nav.analytics")}
          </Button>
          <Button variant="outline" icon={<ScanLine className="h-4 w-4" />} onClick={() => navigate("/scanner")}>
            Scan QR
          </Button>
          <Button icon={<QrCode className="h-4 w-4" />} iconRight={<ArrowRight className="h-4 w-4" />} onClick={() => navigate("/generator")}>
            {t("dashboard.generate")}
          </Button>
        </div>
      </section>

      {summaryError && <p role="alert" className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{summaryError.message}</p>}
      <section aria-label="Personal statistics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card padding="md"><div className="flex items-center justify-between"><div><p className="text-2xl font-bold text-white">{isSummaryLoading ? "—" : summary?.qr_codes ?? 0}</p><p className="text-xs text-slate-600">QR codes · {summary?.favourite_qr_codes ?? 0} favourites</p></div><QrCode className="h-5 w-5 text-violet-400" /></div></Card>
        <Card padding="md"><div className="flex items-center justify-between"><div><p className="text-2xl font-bold text-white">{isSummaryLoading ? "—" : summary?.total_redirect_scans ?? 0}</p><p className="text-xs text-slate-600">Dynamic scans · {summary?.scanner_history ?? 0} decoded</p></div><Activity className="h-5 w-5 text-blue-400" /></div></Card>
        <Card padding="md"><div className="flex items-center justify-between"><div><p className="text-2xl font-bold text-white">{isSummaryLoading ? "—" : summary?.shared_files ?? 0}</p><p className="text-xs text-slate-600">Shared files · {summary?.shared_file_downloads ?? 0} downloads</p></div><FileLock2 className="h-5 w-5 text-emerald-400" /></div></Card>
        <Card padding="md"><div className="flex items-center justify-between"><div><p className="text-2xl font-bold text-white">{isSummaryLoading ? "—" : summary?.exports ?? 0}</p><p className="text-xs text-slate-600">Exports · {summary?.bulk_jobs ?? 0} bulk jobs</p></div><Download className="h-5 w-5 text-amber-400" /></div></Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <Card padding="md"><div className="mb-4 flex items-center gap-2"><Clock3 className="h-4 w-4 text-violet-400" /><h2 className="font-semibold text-white">Recent activity</h2></div>{summary?.recent_activity.length ? <div className="space-y-1">{summary.recent_activity.slice(0, 8).map((event) => <div key={`${event.type}-${event.id}`} className="flex items-start justify-between gap-3 rounded-xl p-2.5 hover:bg-white/3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-300">{event.title}</p><p className="text-xs capitalize text-slate-600">{event.detail}</p></div><span className="whitespace-nowrap text-[11px] text-slate-700">{new Date(event.occurred_at).toLocaleString()}</span></div>)}</div> : <p className="py-8 text-center text-sm text-slate-600">No activity yet</p>}</Card>
        <Card padding="md"><div className="mb-4 flex items-center gap-2"><Download className="h-4 w-4 text-blue-400" /><h2 className="font-semibold text-white">Download history</h2></div>{summary?.download_history.length ? <div className="space-y-1">{summary.download_history.slice(0, 8).map((event) => <div key={event.id} className="flex items-center justify-between gap-3 rounded-xl p-2.5 hover:bg-white/3"><div className="min-w-0"><p className="truncate text-sm text-slate-300">{event.filename}</p><p className="text-xs uppercase text-slate-600">{event.resource_type} · {event.file_format}</p></div><span className="whitespace-nowrap text-[11px] text-slate-700">{new Date(event.downloaded_at).toLocaleString()}</span></div>)}</div> : <p className="py-8 text-center text-sm text-slate-600">Downloaded QR and bulk exports will appear here.</p>}</Card>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-base font-semibold text-white">{t("dashboard.manage")}</h2>
          <p className="mt-1 text-xs text-slate-600">{t("dashboard.manageDesc")}</p>
        </div>

        <Card padding="md">
          <div className="grid gap-3 md:grid-cols-[minmax(220px,1fr)_160px_180px_auto]">
            <Input aria-label="Search QR codes" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search label or destination" icon={<Search className="h-4 w-4" />} />
            <select aria-label="Filter by QR type" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as QrPayloadType | "")} className="h-11 rounded-xl border border-white/8 bg-white/4 px-3 text-sm text-slate-300 focus:border-violet-500/60 focus:outline-none">
              <option value="">All types</option>
              {(["url", "text", "email", "phone", "wifi", "contact", "location"] as QrPayloadType[]).map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
            <select aria-label="Filter by QR status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as QrStatus | "")} className="h-11 rounded-xl border border-white/8 bg-white/4 px-3 text-sm text-slate-300 focus:border-violet-500/60 focus:outline-none">
              <option value="">All statuses</option>
              <option value="active">Active</option><option value="paused">Paused</option><option value="expired">Expired</option><option value="scan_limit_reached">Limit reached</option>
            </select>
            <Button variant={favoritesOnly ? "secondary" : "outline"} icon={<Star className="h-4 w-4" />} onClick={() => setFavoritesOnly((value) => !value)}>
              Favourites
            </Button>
          </div>
        </Card>

        {actionError && <p role="alert" className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{actionError}</p>}

        <Card padding="none" className="overflow-hidden">
          {isLoading ? (
            <div className="flex min-h-48 items-center justify-center"><Spinner /></div>
          ) : error ? (
            <div className="p-10 text-center"><p className="text-sm text-red-400">Could not load QR history.</p><Button variant="ghost" size="sm" className="mt-3" onClick={() => void reload().catch(() => undefined)}>Try again</Button></div>
          ) : items.length === 0 ? (
            <div className="flex min-h-56 flex-col items-center justify-center px-6 text-center"><QrCode className="mb-4 h-8 w-8 text-slate-600" /><h3 className="text-sm font-semibold text-white">No matching QR codes</h3><p className="mt-1 text-xs text-slate-600">Create a QR code or change the current filters.</p></div>
          ) : (
            <div className="divide-y divide-white/5">
              {items.map((item) => (
                <article key={item.id} className="p-5">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="max-w-lg truncate font-medium text-slate-200">{item.label || item.payload_preview}</p>
                        <Badge className="capitalize">{item.type}</Badge>
                        <Badge variant={statusVariant(item.status)} className="capitalize">{item.status.replaceAll("_", " ")}</Badge>
                        <Badge variant="info" className="capitalize">{item.design.gradient_enabled ? "gradient" : item.design.module_style}</Badge>
                        {item.has_logo && <Badge variant="purple">Logo</Badge>}
                        {item.access_mode !== "public" && <Badge variant="purple">SecureVault · {item.access_mode}</Badge>}
                        {item.type === "url" && !item.dynamic_url && <Badge variant="warning">Legacy static</Badge>}
                        {item.is_favorite && <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />}
                      </div>
                      <p className="mt-1 max-w-2xl truncate text-xs text-slate-600">{item.payload_preview}</p>
                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-600">
                        <span>Created {new Date(item.created_at).toLocaleString()}</span>
                        {item.dynamic_url && <span>{item.scan_count}{item.max_scans ? ` / ${item.max_scans}` : ""} scans</span>}
                        {item.expires_at && <span>Expires {new Date(item.expires_at).toLocaleString()}</span>}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      <Button variant="ghost" size="sm" aria-label={item.is_favorite ? "Remove favourite" : "Add favourite"} icon={<Star className={item.is_favorite ? "h-3.5 w-3.5 fill-amber-400 text-amber-400" : "h-3.5 w-3.5"} />} loading={actionId === item.id} onClick={() => void runAction(item.id, () => qrGeneratorApi.update(item.id, { is_favorite: !item.is_favorite }))} />
                      {item.dynamic_url && <Button variant="ghost" size="sm" icon={item.is_active ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />} onClick={() => void runAction(item.id, () => qrGeneratorApi.update(item.id, { is_active: !item.is_active }))}>{item.is_active ? "Pause" : "Activate"}</Button>}
                      <Button variant="ghost" size="sm" icon={<Pencil className="h-3.5 w-3.5" />} onClick={() => startEditing(item)}>Edit</Button>
                      {downloadFormats.map((format) => <Button key={format} variant="ghost" size="sm" onClick={() => void qrGeneratorApi.saveDownload(item.id, format)}>{format.toUpperCase()}</Button>)}
                      <Button variant="danger" size="sm" icon={<Trash2 className="h-3.5 w-3.5" />} onClick={() => { setEditingId(null); setDeleteId(item.id); }}>Delete</Button>
                    </div>
                  </div>

                  {editingId === item.id && (
                    <div className="mt-4 rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">
                      <div className="grid gap-3 md:grid-cols-2">
                        <Input label="Label" value={editForm.label} onChange={(event) => setEditForm((form) => ({ ...form, label: event.target.value }))} />
                        {item.dynamic_url && <Input label="Destination URL" type="url" value={editForm.destinationUrl} onChange={(event) => setEditForm((form) => ({ ...form, destinationUrl: event.target.value }))} />}
                        {item.dynamic_url && <Input label="Expiry date" type="datetime-local" value={editForm.expiresAt} onChange={(event) => setEditForm((form) => ({ ...form, expiresAt: event.target.value }))} />}
                        {item.dynamic_url && <Input label="Maximum scans" type="number" min={1} value={editForm.maxScans} placeholder="Unlimited" onChange={(event) => setEditForm((form) => ({ ...form, maxScans: event.target.value }))} />}
                      </div>
                      <div className="mt-3 flex justify-end gap-2"><Button variant="ghost" size="sm" icon={<X className="h-3.5 w-3.5" />} onClick={() => setEditingId(null)}>Cancel</Button><Button size="sm" loading={actionId === item.id} icon={<Check className="h-3.5 w-3.5" />} onClick={() => void saveEdit(item)}>Save changes</Button></div>
                    </div>
                  )}

                  {deleteId === item.id && (
                    <div className="mt-4 flex flex-col gap-3 rounded-xl border border-red-500/20 bg-red-500/8 p-4 sm:flex-row sm:items-center sm:justify-between">
                      <p className="text-sm text-red-300">Delete this QR record and all locally generated files? This cannot be undone.</p>
                      <div className="flex gap-2"><Button variant="ghost" size="sm" onClick={() => setDeleteId(null)}>Cancel</Button><Button variant="danger" size="sm" loading={actionId === item.id} onClick={() => void runAction(item.id, async () => { await qrGeneratorApi.remove(item.id); setDeleteId(null); })}>Confirm delete</Button></div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </Card>
      </section>
    </div>
  );
};
