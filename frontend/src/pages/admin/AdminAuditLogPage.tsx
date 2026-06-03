import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { ClipboardList } from "lucide-react";

interface AuditLog {
  id: string;
  account_id: string | null;
  actor_id: string | null;
  actor_type: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  meta_data: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export default function AdminAuditLogPage() {
  const { addToast } = useToast();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [perPage] = useState(50);
  const [total, setTotal] = useState(0);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<{
        total: number;
        page: number;
        per_page: number;
        items: AuditLog[];
      }>("/admin/audit-log", {
        params: { page, per_page: perPage },
      });
      setLogs(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load audit log", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page]);

  if (loading && logs.length === 0) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Log</h1>
        <p className="text-sm text-muted">Record of all mutating actions across the platform.</p>
      </div>
      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Time</th>
              <th className="table-header">Actor</th>
              <th className="table-header">Action</th>
              <th className="table-header">Resource</th>
              <th className="table-header">IP</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="table-cell text-center text-muted py-8">
                  <ClipboardList className="mx-auto mb-2" size={24} />
                  No audit logs found.
                </td>
              </tr>
            )}
            {logs.map((l) => (
              <tr key={l.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm">{new Date(l.created_at).toLocaleString()}</td>
                <td className="table-cell text-sm">
                  <span className="badge badge-muted capitalize">{l.actor_type}</span>
                </td>
                <td className="table-cell text-sm font-medium">{l.action}</td>
                <td className="table-cell text-sm">{l.resource_type}{l.resource_id ? `: ${l.resource_id}` : ""}</td>
                <td className="table-cell text-sm">{l.ip_address || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-sm text-muted">
        <div>Showing {logs.length} of {total}</div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <button className="btn-secondary text-xs" disabled={logs.length < perPage} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      </div>
    </div>
  );
}
