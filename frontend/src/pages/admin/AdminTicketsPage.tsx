import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { Link } from "react-router-dom";
import { HelpCircle, CheckSquare, Trash2 } from "lucide-react";

interface Ticket {
  id: string;
  account_id: string;
  title: string;
  status: string;
  priority: string;
  category: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export default function AdminTicketsPage() {
  const { addToast } = useToast();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<{
        total: number;
        page: number;
        per_page: number;
        items: Ticket[];
      }>("/tickets", {
        params: {
          page,
          per_page: perPage,
          status: statusFilter || undefined,
          priority: priorityFilter || undefined,
        },
      });
      setTickets(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load tickets", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page, statusFilter, priorityFilter]);

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      open: "badge-warning",
      waiting_customer: "badge-muted",
      waiting_staff: "badge-accent",
      resolved: "badge-success",
      closed: "badge-muted",
    };
    return map[status] || "badge-muted";
  };

  const priorityBadge = (priority: string) => {
    const map: Record<string, string> = {
      low: "badge-muted",
      normal: "badge-accent",
      high: "badge-warning",
      critical: "badge-danger",
    };
    return map[priority] || "badge-muted";
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const bulkResolve = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    for (const id of ids) {
      try {
        await api.patch(`/tickets/${id}`, { status: "resolved" });
      } catch {
        // ignore per item
      }
    }
    addToast("Bulk resolved", "success");
    setSelected(new Set());
    await load();
  };

  const bulkDelete = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0 || !confirm("Delete selected tickets?")) return;
    for (const id of ids) {
      try {
        await api.delete(`/tickets/${id}`);
      } catch {
        // ignore per item
      }
    }
    addToast("Bulk deleted", "success");
    setSelected(new Set());
    await load();
  };

  if (loading && tickets.length === 0) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ticket Queue</h1>
        <p className="text-sm text-muted">Manage and respond to customer tickets.</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <select className="input w-40" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="waiting_customer">Waiting Customer</option>
          <option value="waiting_staff">Waiting Staff</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
        <select className="input w-40" value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}>
          <option value="">All priorities</option>
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        {selected.size > 0 && (
          <div className="flex items-center gap-2">
            <button className="btn-primary text-xs flex items-center gap-1" onClick={bulkResolve}>
              <CheckSquare size={14} /> Resolve
            </button>
            <button className="btn-danger text-xs flex items-center gap-1" onClick={bulkDelete}>
              <Trash2 size={14} /> Delete
            </button>
          </div>
        )}
      </div>
      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header w-10">
                <input type="checkbox" className="rounded border-border" onChange={(e) => {
                  if (e.target.checked) setSelected(new Set(tickets.map((t) => t.id)));
                  else setSelected(new Set());
                }} checked={selected.size > 0 && selected.size === tickets.length} />
              </th>
              <th className="table-header">Title</th>
              <th className="table-header">Status</th>
              <th className="table-header">Priority</th>
              <th className="table-header">Category</th>
              <th className="table-header">Assigned</th>
              <th className="table-header">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {tickets.length === 0 && (
              <tr>
                <td colSpan={7} className="table-cell text-center text-muted py-8">
                  <HelpCircle className="mx-auto mb-2" size={24} />
                  No tickets found.
                </td>
              </tr>
            )}
            {tickets.map((t) => (
              <tr key={t.id} className="hover:bg-surface-alt/50">
                <td className="table-cell">
                  <input type="checkbox" className="rounded border-border" checked={selected.has(t.id)} onChange={() => toggleSelect(t.id)} />
                </td>
                <td className="table-cell">
                  <Link to={`/admin/tickets/${t.id}`} className="text-sm font-medium text-accent hover:underline">
                    {t.title}
                  </Link>
                </td>
                <td className="table-cell">
                  <span className={`badge ${statusBadge(t.status)}`}>{t.status.replace("_", " ")}</span>
                </td>
                <td className="table-cell">
                  <span className={`badge ${priorityBadge(t.priority)}`}>{t.priority}</span>
                </td>
                <td className="table-cell text-sm capitalize">{t.category}</td>
                <td className="table-cell text-sm">{t.assigned_to || "—"}</td>
                <td className="table-cell text-sm">{new Date(t.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-sm text-muted">
        <div>Showing {tickets.length} of {total}</div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <button className="btn-secondary text-xs" disabled={tickets.length < perPage} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      </div>
    </div>
  );
}
