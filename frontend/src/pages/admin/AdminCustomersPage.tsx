import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { Link } from "react-router-dom";
import { Search, Eye, UserCheck, UserX, Loader2 } from "lucide-react";

interface Customer {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  status: string;
  plan: string;
  totp_enabled: boolean;
  created_at: string;
  updated_at: string;
  stripe_customer_id: string | null;
  domain_count: number;
  mailbox_count: number;
  subscription_status: string | null;
}

export default function AdminCustomersPage() {
  const { isSuperadmin } = useAuth();
  const { addToast } = useToast();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<{
        total: number;
        page: number;
        per_page: number;
        items: Customer[];
      }>("/admin/accounts", {
        params: {
          page,
          per_page: perPage,
          status: statusFilter || undefined,
        },
      });
      setCustomers(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load customers", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page, statusFilter]);

  const filtered = customers.filter((c) => {
    const q = search.toLowerCase();
    return (
      c.email.toLowerCase().includes(q) ||
      (c.display_name || "").toLowerCase().includes(q)
    );
  });

  const suspend = async (id: string, reason: string) => {
    setActionId(id);
    try {
      await api.post(`/admin/accounts/${id}/suspend`, { reason });
      addToast("Account suspended", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to suspend", "error");
    } finally {
      setActionId(null);
    }
  };

  const unsuspend = async (id: string) => {
    setActionId(id);
    try {
      await api.post(`/admin/accounts/${id}/unsuspend`);
      addToast("Account unsuspended", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to unsuspend", "error");
    } finally {
      setActionId(null);
    }
  };

  const impersonate = async (id: string) => {
    try {
      const res = await api.get<{ token: string }>(`/admin/accounts/${id}/impersonate`);
      const token = res.data.token;
      const url = `${window.location.origin}/dashboard?impersonate_token=${token}`;
      window.open(url, "_blank");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to impersonate", "error");
    }
  };

  if (loading && customers.length === 0) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Customer Directory</h1>
        <p className="text-sm text-muted">Search and manage customer accounts.</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[12rem]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            className="input pl-9"
            placeholder="Search by email or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="input w-40"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="cancelled">Cancelled</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Email</th>
              <th className="table-header">Plan</th>
              <th className="table-header">Status</th>
              <th className="table-header">Domains</th>
              <th className="table-header">Mailboxes</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="table-cell text-center text-muted py-8">
                  No customers found.
                </td>
              </tr>
            )}
            {filtered.map((c) => (
              <tr key={c.id} className="hover:bg-surface-alt/50">
                <td className="table-cell">
                  <div className="text-sm font-medium">{c.email}</div>
                  <div className="text-xs text-muted">{c.display_name || "—"}</div>
                </td>
                <td className="table-cell text-sm capitalize">{c.plan}</td>
                <td className="table-cell">
                  <span className={`badge ${c.status === "active" ? "badge-success" : c.status === "suspended" ? "badge-danger" : "badge-muted"}`}>
                    {c.status}
                  </span>
                </td>
                <td className="table-cell text-sm">{c.domain_count}</td>
                <td className="table-cell text-sm">{c.mailbox_count}</td>
                <td className="table-cell text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Link to={`/admin/customers/${c.id}`} className="text-muted hover:text-primary" title="View">
                      <Eye size={16} />
                    </Link>
                    {isSuperadmin && (
                      <button className="text-accent hover:text-accent-hover" title="Impersonate" onClick={() => impersonate(c.id)}>
                        <UserCheck size={16} />
                      </button>
                    )}
                    {c.status === "active" ? (
                      <button
                        className="text-danger hover:opacity-80"
                        title="Suspend"
                        onClick={() => {
                          const reason = prompt("Suspension reason:");
                          if (reason) suspend(c.id, reason);
                        }}
                        disabled={actionId === c.id}
                      >
                        {actionId === c.id ? <Loader2 size={16} className="animate-spin" /> : <UserX size={16} />}
                      </button>
                    ) : (
                      <button
                        className="text-success hover:opacity-80"
                        title="Unsuspend"
                        onClick={() => unsuspend(c.id)}
                        disabled={actionId === c.id}
                      >
                        {actionId === c.id ? <Loader2 size={16} className="animate-spin" /> : <UserCheck size={16} />}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-muted">
        <div>
          Showing {customers.length} of {total}
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <button className="btn-secondary text-xs" disabled={customers.length < perPage} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
