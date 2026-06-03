import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Link } from "react-router-dom";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Globe,
  Plus,
  CheckCircle,
  XCircle,
  Copy,
  RefreshCw,
  Trash2,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Inbox,
  X,
  Save,
} from "lucide-react";

interface Domain {
  id: string;
  domain: string;
  verified: boolean;
  mx_verified: boolean;
  spf_verified: boolean;
  dkim_verified: boolean;
  dkim_selector: string | null;
  mx_record: string | null;
  spf_record: string | null;
  dkim_record: string | null;
  catch_all_target_mailbox_id: string | null;
}

interface MailboxOption {
  id: string;
  local_part: string;
  domain: string;
}

interface OnboardingData {
  domain: string;
  mx_records: string[];
  spf_record: string;
  dkim_selector: string;
  dkim_record: string;
  webmail_url: string;
}

export default function DomainsPage() {
  const { addToast } = useToast();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [mailboxes, setMailboxes] = useState<MailboxOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newDomain, setNewDomain] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [onboarding, setOnboarding] = useState<OnboardingData | null>(null);
  const [onboardingLoading, setOnboardingLoading] = useState(false);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [editingCatchAllId, setEditingCatchAllId] = useState<string | null>(null);
  const [catchAllTarget, setCatchAllTarget] = useState<string>("");
  const [catchAllSaving, setCatchAllSaving] = useState(false);

  const loadDomains = async () => {
    setLoading(true);
    try {
      const [dRes, mRes] = await Promise.all([
        api.get<Domain[]>("/domains"),
        api.get<MailboxOption[]>("/mailboxes"),
      ]);
      setDomains(dRes.data);
      setMailboxes(mRes.data.map((m) => ({ id: m.id, local_part: m.local_part, domain: m.domain || "" })));
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load domains", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDomains();
  }, []);

  const handleAdd = async () => {
    if (!newDomain.trim()) return;
    setAdding(true);
    try {
      await api.post("/domains", { domain: newDomain.trim() });
      addToast("Domain added", "success");
      setNewDomain("");
      await loadDomains();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to add domain", "error");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this domain? This will also remove associated mailboxes.")) return;
    try {
      await api.delete(`/domains/${id}`);
      addToast("Domain deleted", "success");
      await loadDomains();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete domain", "error");
    }
  };

  const handleSetCatchAll = async (domainId: string) => {
    if (!catchAllTarget) return;
    setCatchAllSaving(true);
    try {
      const res = await api.post<Domain>(`/domains/${domainId}/catch-all`, { target_mailbox_id: catchAllTarget });
      setDomains((prev) => prev.map((d) => (d.id === domainId ? res.data : d)));
      addToast("Catch-all set", "success");
      setEditingCatchAllId(null);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to set catch-all", "error");
    } finally {
      setCatchAllSaving(false);
    }
  };

  const handleClearCatchAll = async (domainId: string) => {
    try {
      const res = await api.delete<Domain>(`/domains/${domainId}/catch-all`);
      setDomains((prev) => prev.map((d) => (d.id === domainId ? res.data : d)));
      addToast("Catch-all cleared", "success");
      setEditingCatchAllId(null);
      setCatchAllTarget("");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to clear catch-all", "error");
    }
  };

  const handleVerify = async (id: string) => {
    setVerifyingId(id);
    try {
      const res = await api.post<Domain>(`/domains/${id}/verify`);
      setDomains((prev) => prev.map((d) => (d.id === id ? res.data : d)));
      addToast(res.data.verified ? "Domain verified" : "Verification incomplete. Check DNS records.", res.data.verified ? "success" : "warning");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Verification failed", "error");
    } finally {
      setVerifyingId(null);
    }
  };

  const loadOnboarding = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    setOnboardingLoading(true);
    try {
      const res = await api.get<OnboardingData>(`/domains/${id}/onboarding`);
      setOnboarding(res.data);
    } catch {
      setOnboarding(null);
    } finally {
      setOnboardingLoading(false);
    }
  };

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
    addToast("Copied to clipboard", "success");
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Domains</h1>
          <p className="text-sm text-muted">Manage your domains and DNS records.</p>
        </div>
      </div>

      <div className="card p-4">
        <div className="flex gap-2">
          <input
            type="text"
            className="input flex-1"
            placeholder="example.com"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <button className="btn-primary flex items-center gap-2" onClick={handleAdd} disabled={adding}>
            {adding ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            Add
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {domains.length === 0 && (
          <div className="card p-8 text-center">
            <Globe className="mx-auto text-muted mb-3" size={32} />
            <p className="text-sm text-muted">No domains yet. Add your first domain above.</p>
          </div>
        )}
        {domains.map((d) => (
          <div key={d.id} className="card p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Globe size={18} className="text-accent" />
                <div>
                  <div className="font-semibold text-sm">{d.domain}</div>
                  <div className="flex items-center gap-2 mt-1">
                    {d.verified ? (
                      <span className="badge-success">Verified</span>
                    ) : (
                      <span className="badge-warning">Unverified</span>
                    )}
                    <span className="text-xs text-muted flex items-center gap-1">
                      MX {d.mx_verified ? <CheckCircle size={12} className="text-success" /> : <XCircle size={12} className="text-danger" />}
                      SPF {d.spf_verified ? <CheckCircle size={12} className="text-success" /> : <XCircle size={12} className="text-danger" />}
                      DKIM {d.dkim_verified ? <CheckCircle size={12} className="text-success" /> : <XCircle size={12} className="text-danger" />}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  className="btn-secondary text-xs"
                  onClick={() => handleVerify(d.id)}
                  disabled={verifyingId === d.id}
                >
                  {verifyingId === d.id ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                  Verify
                </button>
                <button
                  className="btn-secondary text-xs"
                  onClick={() => loadOnboarding(d.id)}
                >
                  {expandedId === d.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  DNS
                </button>
                <Link
                  to={`/domains/${d.id}/dns-guide`}
                  className="btn-accent text-xs flex items-center gap-1"
                >
                  <BookOpen size={14} />
                  Setup Guide
                </Link>
                <button className="btn-danger text-xs" onClick={() => handleDelete(d.id)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            {/* Catch-all */}
            <div className="mt-3 border-t border-border pt-3">
              {editingCatchAllId === d.id ? (
                <div className="flex items-center gap-2">
                  <Inbox size={14} className="text-muted" />
                  <select
                    className="input text-xs py-1 flex-1"
                    value={catchAllTarget}
                    onChange={(e) => setCatchAllTarget(e.target.value)}
                  >
                    <option value="">Select mailbox</option>
                    {mailboxes.map((mb) => (
                      <option key={mb.id} value={mb.id}>
                        {mb.local_part}@{mb.domain}
                      </option>
                    ))}
                  </select>
                  <button
                    className="btn-success text-xs flex items-center gap-1"
                    disabled={!catchAllTarget || catchAllSaving}
                    onClick={() => handleSetCatchAll(d.id)}
                  >
                    {catchAllSaving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                    Save
                  </button>
                  <button
                    className="btn-secondary text-xs flex items-center gap-1"
                    onClick={() => { setEditingCatchAllId(null); setCatchAllTarget(""); }}
                  >
                    <X size={12} /> Cancel
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Inbox size={14} className="text-muted" />
                  <span className="text-xs text-muted">
                    Catch-all: {d.catch_all_target_mailbox_id ? (
                      <span className="text-success">
                        {mailboxes.find((m) => m.id === d.catch_all_target_mailbox_id)?.local_part}@
                        {mailboxes.find((m) => m.id === d.catch_all_target_mailbox_id)?.domain || "unknown"}
                      </span>
                    ) : (
                      <span className="text-danger">Disabled</span>
                    )}
                  </span>
                  <button
                    className="text-xs text-accent hover:underline ml-auto"
                    onClick={() => {
                      setEditingCatchAllId(d.id);
                      setCatchAllTarget(d.catch_all_target_mailbox_id || "");
                    }}
                  >
                    {d.catch_all_target_mailbox_id ? "Change" : "Enable"}
                  </button>
                  {d.catch_all_target_mailbox_id && (
                    <button
                      className="text-xs text-danger hover:underline"
                      onClick={() => handleClearCatchAll(d.id)}
                    >
                      Disable
                    </button>
                  )}
                </div>
              )}
            </div>

            {expandedId === d.id && (
              <div className="mt-4 border-t border-border pt-4">
                {onboardingLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 size={20} className="animate-spin text-accent" />
                  </div>
                ) : onboarding ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm text-warning">
                      <AlertTriangle size={16} />
                      Add these DNS records at your registrar to verify and receive mail.
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-muted uppercase">MX Records</div>
                      {onboarding.mx_records.map((rec) => (
                        <div key={rec} className="flex items-center gap-2 bg-surface-alt rounded-lg px-3 py-2 text-sm">
                          <code className="flex-1 font-mono text-xs">{rec}</code>
                          <button className="text-muted hover:text-primary" onClick={() => copy(rec)}>
                            <Copy size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-muted uppercase">SPF Record</div>
                      <div className="flex items-center gap-2 bg-surface-alt rounded-lg px-3 py-2 text-sm">
                        <code className="flex-1 font-mono text-xs">{onboarding.spf_record}</code>
                        <button className="text-muted hover:text-primary" onClick={() => copy(onboarding.spf_record)}>
                          <Copy size={14} />
                        </button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-muted uppercase">DKIM Record</div>
                      <div className="flex items-center gap-2 bg-surface-alt rounded-lg px-3 py-2 text-sm">
                        <code className="flex-1 font-mono text-xs">{onboarding.dkim_record}</code>
                        <button className="text-muted hover:text-primary" onClick={() => copy(onboarding.dkim_record)}>
                          <Copy size={14} />
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-muted">
                      Webmail: <a href={onboarding.webmail_url} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">{onboarding.webmail_url}</a>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted">No onboarding data available.</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
