import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { User, Lock, Key, Shield, Copy, Trash2, Plus, Loader2, CheckCircle, X, Eye } from "lucide-react";

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  permissions: string[];
  last_used_at: string | null;
  created_at: string;
  revoked_at: string | null;
}

export default function SettingsPage() {
  const { account, refresh } = useAuth();
  const { addToast } = useToast();
  const [displayName, setDisplayName] = useState(account?.display_name || "");
  const [profileLoading, setProfileLoading] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeySecret, setNewKeySecret] = useState<string | null>(null);
  const [totpSecret, setTotpSecret] = useState<string | null>(null);
  const [totpUri, setTotpUri] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [showTOTP, setShowTOTP] = useState(false);
  const [showNewKey, setShowNewKey] = useState(false);

  const loadApiKeys = async () => {
    setApiKeysLoading(true);
    try {
      const res = await api.get<ApiKey[]>("/api-keys");
      setApiKeys(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load API keys", "error");
    } finally {
      setApiKeysLoading(false);
    }
  };

  useEffect(() => {
    loadApiKeys();
  }, []);

  const updateProfile = async () => {
    setProfileLoading(true);
    try {
      await api.patch("/auth/me", { display_name: displayName || null });
      addToast("Profile updated", "success");
      await refresh();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update profile", "error");
    } finally {
      setProfileLoading(false);
    }
  };

  const changePassword = async () => {
    setPasswordLoading(true);
    try {
      await api.post("/auth/change-password", { old_password: oldPassword, new_password: newPassword });
      addToast("Password changed", "success");
      setOldPassword("");
      setNewPassword("");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to change password", "error");
    } finally {
      setPasswordLoading(false);
    }
  };

  const createApiKey = async () => {
    if (!newKeyName.trim()) return;
    try {
      const res = await api.post<{ secret: string } & ApiKey>("/api-keys", { name: newKeyName.trim(), permissions: ["smtp", "imap", "api_read"] });
      setNewKeySecret(res.data.secret);
      setNewKeyName("");
      setShowNewKey(true);
      await loadApiKeys();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create API key", "error");
    }
  };

  const revokeApiKey = async (id: string) => {
    if (!confirm("Revoke this API key?")) return;
    try {
      await api.delete(`/api-keys/${id}`);
      addToast("API key revoked", "success");
      await loadApiKeys();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to revoke API key", "error");
    }
  };

  const setupTOTP = async () => {
    try {
      const res = await api.post<{ secret: string; uri: string }>("/auth/totp/setup");
      setTotpSecret(res.data.secret);
      setTotpUri(res.data.uri);
      setShowTOTP(true);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to setup TOTP", "error");
    }
  };

  const verifyTOTP = async () => {
    try {
      await api.post("/auth/totp/verify", { code: totpCode });
      addToast("TOTP enabled", "success");
      setShowTOTP(false);
      setTotpSecret(null);
      setTotpUri(null);
      setTotpCode("");
      await refresh();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Invalid code", "error");
    }
  };

  const disableTOTP = async () => {
    try {
      await api.post("/auth/totp/disable", { code: totpCode });
      addToast("TOTP disabled", "success");
      setTotpCode("");
      await refresh();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Invalid code", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted">Manage your profile, security, and API keys.</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <User size={18} className="text-accent" />
          <h2 className="font-semibold">Profile</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Display name</label>
            <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </div>
          <div className="flex items-end">
            <button className="btn-primary flex items-center gap-2" onClick={updateProfile} disabled={profileLoading}>
              {profileLoading ? <Loader2 size={16} className="animate-spin" /> : "Save"}
            </button>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Lock size={18} className="text-accent" />
          <h2 className="font-semibold">Password</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Current password</label>
            <input type="password" className="input" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
          </div>
          <div>
            <label className="label">New password</label>
            <input type="password" className="input" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} minLength={8} />
          </div>
          <div className="sm:col-span-2 flex justify-end">
            <button className="btn-primary flex items-center gap-2" onClick={changePassword} disabled={passwordLoading}>
              {passwordLoading ? <Loader2 size={16} className="animate-spin" /> : "Change password"}
            </button>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield size={18} className="text-accent" />
          <h2 className="font-semibold">Two-Factor Authentication</h2>
        </div>
        {account?.totp_enabled ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-success text-sm">
              <CheckCircle size={16} /> TOTP is enabled
            </div>
            <div className="flex items-center gap-2">
              <input className="input w-40" placeholder="TOTP code" value={totpCode} onChange={(e) => setTotpCode(e.target.value)} maxLength={6} />
              <button className="btn-danger text-sm" onClick={disableTOTP}>Disable</button>
            </div>
          </div>
        ) : (
          <div>
            {!showTOTP ? (
              <button className="btn-primary text-sm" onClick={setupTOTP}>Enable TOTP</button>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted">Scan this QR code with your authenticator app, then enter the code below.</p>
                {totpUri && (
                  <div className="bg-white p-2 inline-block rounded-lg">
                    <img src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(totpUri)}`} alt="TOTP QR" />
                  </div>
                )}
                <div className="text-xs text-muted font-mono">{totpSecret}</div>
                <div className="flex items-center gap-2">
                  <input className="input w-40" placeholder="TOTP code" value={totpCode} onChange={(e) => setTotpCode(e.target.value)} maxLength={6} />
                  <button className="btn-primary text-sm" onClick={verifyTOTP}>Verify</button>
                  <button className="btn-secondary text-sm" onClick={() => setShowTOTP(false)}>Cancel</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Key size={18} className="text-accent" />
          <h2 className="font-semibold">API Keys</h2>
        </div>
        <div className="flex gap-2 mb-4">
          <input className="input flex-1" placeholder="Key name" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} />
          <button className="btn-primary flex items-center gap-2" onClick={createApiKey}>
            <Plus size={16} /> Create
          </button>
        </div>
        {showNewKey && newKeySecret && (
          <div className="bg-accent/10 text-accent rounded-lg px-4 py-3 mb-4 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye size={16} />
              <span className="font-mono">{newKeySecret}</span>
            </div>
            <div className="flex items-center gap-2">
              <button className="text-accent hover:text-accent-hover" onClick={() => { navigator.clipboard.writeText(newKeySecret); addToast("Copied", "success"); }}>
                <Copy size={14} />
              </button>
              <button className="text-accent hover:text-accent-hover" onClick={() => setShowNewKey(false)}>
                <X size={14} />
              </button>
            </div>
          </div>
        )}
        <div className="space-y-2">
          {apiKeysLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 size={20} className="animate-spin text-accent" />
            </div>
          ) : apiKeys.length === 0 ? (
            <p className="text-sm text-muted">No API keys yet.</p>
          ) : (
            apiKeys.map((k) => (
              <div key={k.id} className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2">
                <div>
                  <div className="text-sm font-medium">{k.name}</div>
                  <div className="text-xs text-muted font-mono">{k.prefix}... · {k.permissions.join(", ")}</div>
                </div>
                <button className="text-danger hover:opacity-80" onClick={() => revokeApiKey(k.id)}>
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
