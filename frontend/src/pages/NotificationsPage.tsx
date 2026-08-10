import { useEffect, useState } from "react";
import { AlertTriangle, Bell, CheckCheck, ExternalLink, Mail, RefreshCw, ShieldAlert, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Badge, Button, Card, Spinner } from "../components/ui";
import { useNotifications, type NotificationPreferencesUpdate, type NotificationSeverity } from "../features/notifications";


const severityBadge: Record<NotificationSeverity, "info" | "success" | "warning" | "danger"> = {
  info: "info", success: "success", warning: "warning", critical: "danger",
};

export function NotificationsPage() {
  const navigate = useNavigate();
  const [unreadOnly, setUnreadOnly] = useState(false);
  const { data, preferences, loading, saving, error, reload, markRead, markAllRead, deleteNotification, savePreferences } = useNotifications(unreadOnly);
  const [draft, setDraft] = useState<NotificationPreferencesUpdate | null>(null);
  useEffect(() => { if (preferences) { const { local_smtp_available: _, ...values } = preferences; setDraft(values); } }, [preferences]);
  const toggle = (key: keyof NotificationPreferencesUpdate) => setDraft((value) => value ? { ...value, [key]: !value[key] } : value);

  return <div className="mx-auto max-w-6xl space-y-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><Badge variant="purple">Local alerts</Badge><h1 className="mt-3 text-2xl font-bold text-white">Notifications</h1><p className="mt-1 text-sm text-slate-500">Security, QR, bulk generation, and secure-sharing events from your local IntelliQR instance.</p></div><div className="flex gap-2"><Button variant="ghost" icon={<RefreshCw className="h-4 w-4" />} onClick={() => void reload()} loading={loading}>Refresh</Button><Button variant="outline" icon={<CheckCheck className="h-4 w-4" />} disabled={!data?.unread_count} onClick={() => void markAllRead()}>Read all</Button></div></div>
    {error && <Card padding="sm" className="border-red-500/20 bg-red-500/5 text-sm text-red-300">{error}</Card>}

    <div className="grid gap-6 lg:grid-cols-[1.5fr_0.8fr]">
      <Card padding="none">
        <div className="flex items-center justify-between border-b border-white/6 p-5"><div><h2 className="font-semibold text-white">Event inbox</h2><p className="mt-1 text-xs text-slate-600">{data?.unread_count ?? 0} unread notification{data?.unread_count === 1 ? "" : "s"}</p></div><label className="flex items-center gap-2 text-xs text-slate-400"><input type="checkbox" checked={unreadOnly} onChange={(event) => setUnreadOnly(event.target.checked)} className="accent-violet-500" />Unread only</label></div>
        {loading && !data ? <div className="flex justify-center p-16"><Spinner size="lg" /></div> : <div className="divide-y divide-white/5">
          {data?.items.map((item) => <article key={item.id} className={`p-5 ${item.is_read ? "opacity-70" : "bg-violet-500/[0.025]"}`}>
            <div className="flex items-start gap-3"><span className={`mt-0.5 rounded-xl p-2 ${item.severity === "critical" ? "bg-red-500/10 text-red-400" : "bg-violet-500/10 text-violet-400"}`}>{item.category === "security" ? <ShieldAlert className="h-4 w-4" /> : <Bell className="h-4 w-4" />}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-medium text-slate-200">{item.title}</h3><Badge variant={severityBadge[item.severity]}>{item.severity}</Badge>{!item.is_read && <span className="h-2 w-2 rounded-full bg-violet-400" aria-label="Unread" />}</div><p className="mt-1 text-sm leading-6 text-slate-500">{item.message}</p><p className="mt-2 text-xs text-slate-700">{new Date(item.created_at).toLocaleString()}</p></div><div className="flex gap-1">{item.action_url && <button aria-label="Open related page" className="rounded-lg p-2 text-slate-600 hover:bg-white/5 hover:text-violet-300" onClick={() => { if (!item.is_read) void markRead(item.id); navigate(item.action_url!); }}><ExternalLink className="h-4 w-4" /></button>}{!item.is_read && <button aria-label="Mark notification read" className="rounded-lg p-2 text-slate-600 hover:bg-white/5 hover:text-emerald-400" onClick={() => void markRead(item.id)}><CheckCheck className="h-4 w-4" /></button>}<button aria-label="Delete notification" className="rounded-lg p-2 text-slate-600 hover:bg-red-500/5 hover:text-red-400" onClick={() => void deleteNotification(item.id)}><Trash2 className="h-4 w-4" /></button></div></div>
          </article>)}
          {!data?.items.length && <div className="p-14 text-center"><Bell className="mx-auto h-8 w-8 text-slate-700" /><p className="mt-3 text-sm text-slate-500">No notifications to show.</p></div>}
        </div>}
      </Card>

      <Card><div className="flex items-center gap-3"><span className="rounded-xl bg-blue-500/10 p-2.5"><Mail className="h-5 w-5 text-blue-400" /></span><div><h2 className="font-semibold text-white">Delivery preferences</h2><p className="text-xs text-slate-600">Stored with your account.</p></div></div>
        {draft && <div className="mt-5 space-y-3">
          {[{ key: "in_app_enabled", label: "In-app notifications" }, { key: "email_enabled", label: "Local email delivery", disabled: !preferences?.local_smtp_available }, { key: "security_alerts", label: "Security alerts" }, { key: "qr_activity", label: "QR activity" }, { key: "share_activity", label: "ShareVault activity" }, { key: "bulk_activity", label: "BulkForge results" }].map(({ key, label, disabled }) => <label key={key} className={`flex items-center justify-between rounded-xl border border-white/6 p-3 text-sm ${disabled ? "opacity-50" : "text-slate-300"}`}><span>{label}</span><input type="checkbox" checked={draft[key as keyof NotificationPreferencesUpdate]} disabled={disabled} onChange={() => toggle(key as keyof NotificationPreferencesUpdate)} className="h-4 w-4 accent-violet-500" /></label>)}
          {!preferences?.local_smtp_available && <p className="flex gap-2 rounded-xl bg-amber-500/5 p-3 text-xs leading-5 text-amber-400"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />Start a localhost SMTP capture server and configure the backend to enable email.</p>}
          <Button fullWidth loading={saving} onClick={() => void savePreferences(draft)}>Save preferences</Button>
        </div>}
      </Card>
    </div>
  </div>;
}
