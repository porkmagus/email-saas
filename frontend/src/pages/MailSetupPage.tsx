import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Mail, Globe, ExternalLink, Copy, Server, Shield, Smartphone } from "lucide-react";

interface DomainSetup {
  id: string;
  domain: string;
  verified: boolean;
  webmail_url: string;
  mx_records: string[];
  spf_record: string;
  dkim_selector: string;
  dkim_record: string;
}

interface MailboxSetup {
  id: string;
  local_part: string;
  domain: string;
  display_name: string | null;
}

export default function MailSetupPage() {
  const { addToast } = useToast();
  const [domains, setDomains] = useState<DomainSetup[]>([]);
  const [mailboxes, setMailboxes] = useState<MailboxSetup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [domRes, mbRes] = await Promise.all([
          api.get<DomainSetup[]>("/domains"),
          api.get<MailboxSetup[]>("/mailboxes"),
        ]);
        setDomains(domRes.data);
        setMailboxes(mbRes.data);
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Failed to load setup info", "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [addToast]);

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
    addToast("Copied to clipboard", "success");
  };

  if (loading) return <Loading />;

  const verifiedDomains = domains.filter((d) => d.verified);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Email Setup</h1>
        <p className="text-sm text-muted">Connect your email client or use webmail.</p>
      </div>

      {/* Webmail Section */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Globe size={20} className="text-accent" />
          <h2 className="font-semibold">Webmail Access</h2>
        </div>
        {verifiedDomains.length === 0 ? (
          <p className="text-sm text-muted">Verify a domain first to access webmail.</p>
        ) : (
          <div className="space-y-3">
            {verifiedDomains.map((d) => (
              <div key={d.id} className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-surface-alt transition-colors">
                <div>
                  <div className="font-medium text-sm">{d.domain}</div>
                  <div className="text-xs text-muted">Roundcube webmail</div>
                </div>
                <a
                  href={d.webmail_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary text-sm flex items-center gap-2"
                >
                  <ExternalLink size={14} />
                  Open Webmail
                </a>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* IMAP/SMTP Settings */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Server size={20} className="text-accent" />
          <h2 className="font-semibold">Email Client Settings</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Mail size={16} className="text-accent" />
              Incoming (IMAP)
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Server</span>
                <div className="flex items-center gap-2">
                  <code className="font-mono text-xs">mail.{verifiedDomains[0]?.domain || "yourdomain.com"}</code>
                  <button onClick={() => copy(`mail.${verifiedDomains[0]?.domain || "yourdomain.com"}`)}>
                    <Copy size={14} className="text-muted hover:text-primary" />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Port</span>
                <code className="font-mono text-xs">993</code>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Security</span>
                <span className="text-xs">SSL/TLS</span>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Username</span>
                <span className="text-xs text-muted">Your full email address</span>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Password</span>
                <span className="text-xs text-muted">Your mailbox password</span>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Smartphone size={16} className="text-accent" />
              Outgoing (SMTP)
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Server</span>
                <div className="flex items-center gap-2">
                  <code className="font-mono text-xs">mail.{verifiedDomains[0]?.domain || "yourdomain.com"}</code>
                  <button onClick={() => copy(`mail.${verifiedDomains[0]?.domain || "yourdomain.com"}`)}>
                    <Copy size={14} className="text-muted hover:text-primary" />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Port</span>
                <code className="font-mono text-xs">587</code>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Security</span>
                <span className="text-xs">STARTTLS</span>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Authentication</span>
                <span className="text-xs">Normal password</span>
              </div>
              <div className="flex items-center justify-between bg-surface-alt rounded-lg px-3 py-2 text-sm">
                <span className="text-muted">Username</span>
                <span className="text-xs text-muted">Your full email address</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mailbox List */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield size={20} className="text-accent" />
          <h2 className="font-semibold">Your Mailboxes</h2>
        </div>
        {mailboxes.length === 0 ? (
          <p className="text-sm text-muted">No mailboxes yet. Create one in the Mailboxes section.</p>
        ) : (
          <div className="space-y-2">
            {mailboxes.map((mb) => (
              <div key={mb.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                <div>
                  <div className="font-medium text-sm">
                    {mb.local_part}@{mb.domain}
                  </div>
                  <div className="text-xs text-muted">{mb.display_name || "—"}</div>
                </div>
                <button
                  onClick={() => copy(`${mb.local_part}@${mb.domain}`)}
                  className="text-muted hover:text-primary"
                  title="Copy address"
                >
                  <Copy size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
