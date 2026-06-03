import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Mail,
  Globe,
  Activity,
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  ListChecks,
} from "lucide-react";
import { Link } from "react-router-dom";

interface Stats {
  domain_count: number;
  mailbox_count: number;
  verified_domains: number;
  usage: {
    emails_sent: number;
    storage_bytes: number;
  };
  plan: string;
  status: string;
}

export default function DashboardPage() {
  const { account } = useAuth();
  const { addToast } = useToast();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [domainsRes, mailboxesRes] = await Promise.all([
          api.get<{ id: string; verified: boolean }[]>("/domains"),
          api.get<{ id: string }[]>("/mailboxes"),
        ]);
        const domains = domainsRes.data;
        const mailboxes = mailboxesRes.data;
        const verified = domains.filter((d) => d.verified).length;
        setStats({
          domain_count: domains.length,
          mailbox_count: mailboxes.length,
          verified_domains: verified,
          usage: { emails_sent: 0, storage_bytes: 0 },
          plan: account?.plan || "starter",
          status: account?.status || "active",
        });
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Failed to load dashboard", "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [account, addToast]);

  if (loading) return <Loading />;

  const isSuspended = account?.status === "suspended";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted">Welcome back, {account?.display_name || account?.email}.</p>
      </div>

      {isSuspended && (
        <div className="bg-danger/10 text-danger rounded-lg px-4 py-3 flex items-center gap-3 text-sm">
          <AlertTriangle size={18} />
          Your account is suspended. Please check your billing or contact support.
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 flex items-center gap-4">
          <div className="bg-accent/10 p-3 rounded-lg text-accent">
            <Globe size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold">{stats?.domain_count || 0}</div>
            <div className="text-xs text-muted">Domains</div>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-4">
          <div className="bg-accent/10 p-3 rounded-lg text-accent">
            <Mail size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold">{stats?.mailbox_count || 0}</div>
            <div className="text-xs text-muted">Mailboxes</div>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-4">
          <div className="bg-success/10 p-3 rounded-lg text-success">
            <CheckCircle size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold">{stats?.verified_domains || 0}</div>
            <div className="text-xs text-muted">Verified domains</div>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-4">
          <div className="bg-warning/10 p-3 rounded-lg text-warning">
            <Activity size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold capitalize">{stats?.plan}</div>
            <div className="text-xs text-muted">Plan</div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Quick Actions</h2>
          </div>
          <div className="space-y-2">
            <Link to="/domains" className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-surface-alt transition-colors">
              <span className="text-sm font-medium">Add a domain</span>
              <ArrowRight size={16} className="text-muted" />
            </Link>
            <Link to="/mailboxes" className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-surface-alt transition-colors">
              <span className="text-sm font-medium">Create a mailbox</span>
              <ArrowRight size={16} className="text-muted" />
            </Link>
            <Link to="/tickets" className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-surface-alt transition-colors">
              <span className="text-sm font-medium">Open a support ticket</span>
              <ArrowRight size={16} className="text-muted" />
            </Link>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Onboarding</h2>
            <Link to="/onboarding" className="text-sm text-accent hover:underline flex items-center gap-1">
              View checklist <ListChecks size={14} />
            </Link>
          </div>
          <div className="w-full bg-border rounded-full h-2 mb-2">
            <div
              className="bg-accent h-2 rounded-full transition-all"
              style={{ width: `${Math.min(100, (stats?.verified_domains || 0) * 33 + (stats?.mailbox_count || 0) * 33)}%` }}
            />
          </div>
          <p className="text-xs text-muted">Complete your setup to get the most out of your account.</p>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-4">Recent Activity</h2>
        <p className="text-sm text-muted">Activity logging and provisioning jobs will appear here.</p>
      </div>
    </div>
  );
}
