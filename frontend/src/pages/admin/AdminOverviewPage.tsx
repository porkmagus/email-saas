import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { Users, Globe, Mail, AlertTriangle, DollarSign, TrendingUp } from "lucide-react";

interface AdminStats {
  total_accounts: number;
  active_accounts: number;
  suspended_accounts: number;
  total_domains: number;
  verified_domains: number;
  total_mailboxes: number;
  open_tickets: number;
  mrr_estimate_cents: number;
}

export default function AdminOverviewPage() {
  const { addToast } = useToast();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get<AdminStats>("/admin/stats");
        setStats(res.data);
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Failed to load stats", "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [addToast]);

  if (loading) return <Loading />;

  const cards = [
    { label: "Total Accounts", value: stats?.total_accounts ?? 0, icon: Users, color: "text-accent" },
    { label: "Active Accounts", value: stats?.active_accounts ?? 0, icon: TrendingUp, color: "text-success" },
    { label: "Suspended", value: stats?.suspended_accounts ?? 0, icon: AlertTriangle, color: "text-danger" },
    { label: "Domains", value: stats?.total_domains ?? 0, icon: Globe, color: "text-accent" },
    { label: "Verified Domains", value: stats?.verified_domains ?? 0, icon: Globe, color: "text-success" },
    { label: "Mailboxes", value: stats?.total_mailboxes ?? 0, icon: Mail, color: "text-accent" },
    { label: "Open Tickets", value: stats?.open_tickets ?? 0, icon: AlertTriangle, color: "text-warning" },
    {
      label: "MRR Estimate",
      value: `$${((stats?.mrr_estimate_cents ?? 0) / 100).toFixed(2)}`,
      icon: DollarSign,
      color: "text-success",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin Overview</h1>
        <p className="text-sm text-muted">Global KPIs and health metrics.</p>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="card p-4 flex items-center gap-4">
            <div className={`bg-surface-alt p-3 rounded-lg ${c.color}`}>
              <c.icon size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold">{c.value}</div>
              <div className="text-xs text-muted">{c.label}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="card p-6">
        <h2 className="font-semibold mb-2">Recent Activity</h2>
        <p className="text-sm text-muted">Admin actions and audit log will be shown here.</p>
      </div>
    </div>
  );
}
