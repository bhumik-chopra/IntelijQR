import React, { useEffect, useState } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, LogIn, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Badge, Button, Card, Input, Spinner } from "../components/ui";
import { useAuth } from "../features/auth";
import { vaultApi, type VaultPolicy } from "../features/secure-vault";


export const VaultAccessPage: React.FC = () => {
  const { slug = "" } = useParams();
  const { isAuthenticated, isInitializing, user } = useAuth();
  const [policy, setPolicy] = useState<VaultPolicy | null>(null);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    vaultApi.policy(slug).then(setPolicy).catch((caught) => setError(caught instanceof Error ? caught.message : "Protected QR code was not found"));
  }, [slug]);

  const unlock = async () => {
    setLoading(true); setError(null);
    try {
      const grant = await vaultApi.unlock(slug, password);
      window.location.assign(grant.redirect_url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "SecureVault access failed");
    } finally { setLoading(false); }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#08080F] px-5 py-10">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,rgba(124,58,237,0.18),transparent_48%)]" />
      <Card glow padding="lg" className="relative w-full max-w-md">
        {!policy && !error ? <div className="flex min-h-64 items-center justify-center"><Spinner size="lg" /></div> : <>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-blue-500 shadow-lg shadow-violet-900/40"><LockKeyhole className="h-7 w-7 text-white" /></div>
          <div className="mt-5 text-center"><Badge variant="purple"><ShieldCheck className="h-3.5 w-3.5" /> SecureVault</Badge><h1 className="mt-4 text-2xl font-bold text-white">{policy?.label ?? "Protected destination"}</h1><p className="mt-2 text-sm text-slate-500">This QR destination is protected. Complete the access check to continue.</p></div>
          {error && <p role="alert" className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{error}</p>}
          {policy?.access_mode === "password" && <div className="mt-6"><Input label="Access password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} icon={<LockKeyhole className="h-4 w-4" />} iconRight={showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />} onIconRightClick={() => setShowPassword((value) => !value)} autoComplete="current-password" /></div>}
          {policy?.requires_authentication && !isInitializing && !isAuthenticated ? <Link to="/login" state={{ from: { pathname: `/access/${slug}` } }} className="mt-6 block"><Button fullWidth icon={<LogIn className="h-4 w-4" />}>Sign in to continue</Button></Link> : policy && <Button fullWidth className="mt-6" loading={loading} disabled={policy.access_mode === "password" && password.length < 8} iconRight={<ArrowRight className="h-4 w-4" />} onClick={() => void unlock()}>{policy.access_mode === "private" ? `Continue as ${user?.email ?? "member"}` : "Unlock destination"}</Button>}
          <p className="mt-5 text-center text-xs text-slate-700">Access grants expire quickly and are valid only for this QR code.</p>
        </>}
      </Card>
    </main>
  );
};
