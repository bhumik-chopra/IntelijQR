export interface VaultPolicy {
  slug: string;
  label: string;
  access_mode: "public" | "password" | "authenticated" | "private";
  requires_authentication: boolean;
  status: string;
}

export interface VaultGrant {
  redirect_url: string;
  expires_at: string;
}
