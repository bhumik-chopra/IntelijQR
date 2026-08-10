import { useMemo, useState, type FormEvent } from "react";
import { Activity, Ban, CheckCircle2, Database, QrCode, RefreshCw, Search, ShieldCheck, Users } from "lucide-react";

import { Badge, Button, Card, Input, Spinner } from "../components/ui";
import { useAdminDashboard, type AdminUserFilters } from "../features/admin";
import { useAuth } from "../features/auth";


const number = new Intl.NumberFormat();

export function AdminPage() {
  const { user: currentUser } = useAuth();
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState<AdminUserFilters>({ limit: 20, offset: 0 });
  const stableFilters = useMemo(() => filters, [filters.limit, filters.offset, filters.role, filters.search, filters.status]);
  const { overview, users, loading, mutatingUserId, error, reload, updateUser } = useAdminDashboard(stableFilters);

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    setFilters((value) => ({ ...value, search: searchInput.trim() || undefined, offset: 0 }));
  };

  const confirmChange = (message: string, action: () => void) => {
    if (window.confirm(message)) action();
  };

  const stats = overview?.stats;
  const statCards = [
    { label: "Users", value: stats?.users ?? 0, detail: `${stats?.active_users ?? 0} active`, icon: Users },
    { label: "QR codes", value: stats?.qr_codes ?? 0, detail: `${stats?.dynamic_scans ?? 0} redirect scans`, icon: QrCode },
    { label: "Decoded scans", value: stats?.decoded_scans ?? 0, detail: `${stats?.active_admins ?? 0} administrators`, icon: Activity },
    { label: "Shared files", value: stats?.shared_files ?? 0, detail: `${stats?.share_downloads ?? 0} downloads`, icon: Database },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-violet-400" /><Badge variant="purple">Administrator</Badge></div>
          <h1 className="mt-2 text-2xl font-bold text-white">Platform control center</h1>
          <p className="mt-1 text-sm text-slate-500">Monitor local usage and control account access without viewing private content.</p>
        </div>
        <Button variant="outline" icon={<RefreshCw className="h-4 w-4" />} onClick={() => void reload()} loading={loading}>Refresh</Button>
      </div>

      {error && <Card padding="sm" className="border-red-500/20 bg-red-500/5 text-sm text-red-300">{error}</Card>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map(({ label, value, detail, icon: Icon }) => (
          <Card key={label} padding="sm">
            <div className="flex items-start justify-between"><div><p className="text-xs uppercase tracking-wider text-slate-600">{label}</p><p className="mt-2 text-2xl font-bold text-white">{number.format(value)}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></div><span className="rounded-xl bg-violet-500/10 p-2.5"><Icon className="h-5 w-5 text-violet-400" /></span></div>
          </Card>
        ))}
      </section>

      <Card padding="none">
        <div className="border-b border-white/7 p-4 sm:p-5">
          <h2 className="font-semibold text-white">User access management</h2>
          <div className="mt-4 flex flex-col gap-3 lg:flex-row">
            <form onSubmit={submitSearch} className="flex flex-1 gap-2">
              <Input aria-label="Search users" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Search name or email" icon={<Search className="h-4 w-4" />} />
              <Button type="submit" variant="secondary">Search</Button>
            </form>
            <select aria-label="Filter by role" value={filters.role ?? ""} onChange={(event) => setFilters((value) => ({ ...value, role: (event.target.value || undefined) as AdminUserFilters["role"], offset: 0 }))} className="h-11 rounded-xl border border-white/8 bg-white/4 px-3 text-sm text-slate-300 outline-none">
              <option value="">All roles</option><option value="user">Members</option><option value="admin">Admins</option>
            </select>
            <select aria-label="Filter by status" value={filters.status ?? ""} onChange={(event) => setFilters((value) => ({ ...value, status: (event.target.value || undefined) as AdminUserFilters["status"], offset: 0 }))} className="h-11 rounded-xl border border-white/8 bg-white/4 px-3 text-sm text-slate-300 outline-none">
              <option value="">All statuses</option><option value="active">Active</option><option value="disabled">Disabled</option>
            </select>
          </div>
        </div>

        {loading && !users ? <div className="flex justify-center p-12"><Spinner size="lg" /></div> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left text-sm">
              <thead className="border-b border-white/6 text-xs uppercase tracking-wide text-slate-600"><tr><th className="px-5 py-3">Account</th><th className="px-5 py-3">Role</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Joined</th><th className="px-5 py-3 text-right">Actions</th></tr></thead>
              <tbody className="divide-y divide-white/5">
                {users?.items.map((account) => {
                  const isSelf = account.id === currentUser?.id;
                  const busy = mutatingUserId === account.id;
                  return <tr key={account.id} className="text-slate-400">
                    <td className="px-5 py-4"><p className="font-medium text-slate-200">{account.name}{isSelf && <span className="ml-2 text-xs text-violet-400">You</span>}</p><p className="text-xs text-slate-600">{account.email}</p></td>
                    <td className="px-5 py-4"><Badge variant={account.role === "admin" ? "purple" : "default"}>{account.role}</Badge></td>
                    <td className="px-5 py-4"><span className={account.status === "active" ? "text-emerald-400" : "text-red-400"}>{account.status}</span></td>
                    <td className="px-5 py-4 text-xs">{new Date(account.created_at).toLocaleDateString()}</td>
                    <td className="px-5 py-4"><div className="flex justify-end gap-2">
                      <Button size="sm" variant="outline" disabled={isSelf || busy} onClick={() => confirmChange(`${account.role === "admin" ? "Remove administrator access from" : "Make administrator"} ${account.email}?`, () => void updateUser(account.id, { role: account.role === "admin" ? "user" : "admin" }))}>{account.role === "admin" ? "Make member" : "Make admin"}</Button>
                      <Button size="sm" variant={account.status === "active" ? "danger" : "secondary"} disabled={isSelf || busy} icon={account.status === "active" ? <Ban className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />} onClick={() => confirmChange(`${account.status === "active" ? "Disable" : "Enable"} ${account.email}? Active sessions will be revoked.`, () => void updateUser(account.id, { status: account.status === "active" ? "disabled" : "active" }))}>{account.status === "active" ? "Disable" : "Enable"}</Button>
                    </div></td>
                  </tr>;
                })}
                {!users?.items.length && <tr><td colSpan={5} className="p-10 text-center text-slate-600">No accounts match these filters.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
        {users && <div className="flex items-center justify-between border-t border-white/6 px-5 py-3 text-xs text-slate-500"><span>{users.total} accounts</span><div className="flex gap-2"><Button size="sm" variant="ghost" disabled={users.offset === 0} onClick={() => setFilters((value) => ({ ...value, offset: Math.max(0, (value.offset ?? 0) - (value.limit ?? 20)) }))}>Previous</Button><Button size="sm" variant="ghost" disabled={!users.has_more} onClick={() => setFilters((value) => ({ ...value, offset: (value.offset ?? 0) + (value.limit ?? 20) }))}>Next</Button></div></div>}
      </Card>

      <Card>
        <h2 className="font-semibold text-white">Recent administrative audit</h2>
        <div className="mt-4 space-y-3">
          {overview?.recent_audit.map((event) => <div key={event.id} className="flex items-start justify-between gap-4 rounded-xl border border-white/6 bg-white/[0.02] p-3"><div><p className="text-sm text-slate-300">User access updated</p><p className="mt-1 font-mono text-xs text-slate-600">Target {event.target_id}</p></div><div className="text-right"><p className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</p><p className="mt-1 text-xs text-violet-400">{Object.entries(event.details).map(([key, value]) => `${key}: ${value}`).join(" · ")}</p></div></div>)}
          {!overview?.recent_audit.length && <p className="py-6 text-center text-sm text-slate-600">No administrative changes recorded yet.</p>}
        </div>
      </Card>
    </div>
  );
}
