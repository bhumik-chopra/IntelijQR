import { useEffect, useState } from "react";
import { CalendarDays, KeyRound, Mail, Save, ShieldCheck, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Avatar, Badge, Button, Card, Input } from "../components/ui";
import { authApi, useAuth } from "../features/auth";
import { LanguageSelector, type Locale } from "../features/i18n";
import { useTheme } from "../hooks/useTheme";


export function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name ?? "");
  const [profileLoading, setProfileLoading] = useState(false);
  const [passwords, setPasswords] = useState({ current: "", next: "", confirm: "" });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { if (user) setName(user.name); }, [user]);

  const saveProfile = async () => {
    if (name.trim().length < 2) return;
    setProfileLoading(true); setError(null);
    try { await authApi.updateProfile(name.trim()); await refreshUser(); setMessage("Profile updated."); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Profile update failed"); }
    finally { setProfileLoading(false); }
  };

  const changePassword = async () => {
    setError(null);
    if (passwords.next.length < 8) { setError("New password must contain at least 8 characters."); return; }
    if (passwords.next !== passwords.confirm) { setError("New passwords do not match."); return; }
    setPasswordLoading(true);
    try {
      await authApi.changePassword(passwords.current, passwords.next);
      await logout().catch(() => undefined);
      navigate("/login", { replace: true, state: { passwordChanged: true } });
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Password change failed"); }
    finally { setPasswordLoading(false); }
  };

  const changeLocale = async (locale: Locale) => {
    setError(null);
    try { await authApi.updateLocale(locale); await refreshUser(); setMessage("Language preference updated."); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Language update failed"); }
  };

  return <div className="mx-auto max-w-5xl space-y-6 animate-fade-in">
    <section><Badge variant="purple">Personal account</Badge><h1 className="mt-3 text-2xl font-bold text-white sm:text-3xl">Profile & settings</h1><p className="mt-1 text-sm text-slate-500">Manage your identity, password, language, and local appearance.</p></section>
    {message && <p className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-400">{message}</p>}
    {error && <p role="alert" className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{error}</p>}
    <div className="grid gap-6 lg:grid-cols-2">
      <Card padding="lg">
        <div className="flex items-center gap-4"><Avatar name={user?.name ?? "User"} size="lg" /><div><h2 className="font-semibold text-white">Account profile</h2><Badge variant="success" className="mt-1 capitalize">{user?.role ?? "member"}</Badge></div></div>
        <div className="mt-6 space-y-4"><Input label="Display name" value={name} onChange={(event) => setName(event.target.value)} icon={<UserRound className="h-4 w-4" />} /><Input label="Email address" value={user?.email ?? ""} disabled icon={<Mail className="h-4 w-4" />} /><Button loading={profileLoading} disabled={name.trim() === user?.name || name.trim().length < 2} icon={<Save className="h-4 w-4" />} onClick={() => void saveProfile()}>Save profile</Button></div>
        <div className="mt-6 border-t border-white/6 pt-4 text-xs text-slate-600"><p className="flex items-center gap-2"><CalendarDays className="h-3.5 w-3.5" />Member since {user ? new Date(user.created_at).toLocaleDateString() : "—"}</p><p className="mt-2 flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5" />Last login {user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Not recorded"}</p></div>
      </Card>
      <Card padding="lg">
        <div><h2 className="font-semibold text-white">Change password</h2><p className="text-xs text-slate-600">This signs your account out on every device.</p></div>
        <div className="mt-6 space-y-4"><Input label="Current password" type="password" value={passwords.current} onChange={(event) => setPasswords((value) => ({ ...value, current: event.target.value }))} icon={<KeyRound className="h-4 w-4" />} /><Input label="New password" type="password" value={passwords.next} onChange={(event) => setPasswords((value) => ({ ...value, next: event.target.value }))} /><Input label="Confirm new password" type="password" value={passwords.confirm} onChange={(event) => setPasswords((value) => ({ ...value, confirm: event.target.value }))} /><Button variant="secondary" loading={passwordLoading} disabled={!passwords.current || !passwords.next || !passwords.confirm} icon={<KeyRound className="h-4 w-4" />} onClick={() => void changePassword()}>Change password</Button></div>
        <div className="mt-8 border-t border-white/6 pt-5"><h3 className="text-sm font-medium text-slate-300">Appearance</h3><p className="mt-1 text-xs text-slate-600">Theme preference stays on this local browser.</p><Button className="mt-3" variant="outline" onClick={toggleTheme}>Switch to {theme === "dark" ? "light" : "dark"} theme</Button><h3 className="mb-2 mt-5 text-sm font-medium text-slate-300">Interface language</h3><LanguageSelector onLocaleChange={(locale) => void changeLocale(locale)} /></div>
      </Card>
    </div>
  </div>;
}
