import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { Wrench, RefreshCw } from "lucide-react";

interface Job {
  id: string;
  account_id: string;
  type: string;
  payload: Record<string, unknown>;
  status: string;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export default function AdminJobsPage() {
  const { addToast } = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<{
        total: number;
        page: number;
        per_page: number;
        items: Job[];
      }>("/admin/jobs", {
        params: {
          page,
          per_page: perPage,
          status: statusFilter || undefined,
        },
      });
      setJobs(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load jobs", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page, statusFilter]);

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: "badge-warning",
      running: "badge-accent",
      completed: "badge-success",
      failed: "badge-danger",
      retrying: "badge-warning",
    };
    return map[status] || "badge-muted";
  };

  if (loading && jobs.length === 0) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Provisioning Monitor</h1>
        <p className="text-sm text-muted">Queue status and job history.</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <select
          className="input w-48"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="retrying">Retrying</option>
        </select>
        <button className="btn-secondary flex items-center gap-2" onClick={load}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Type</th>
              <th className="table-header">Status</th>
              <th className="table-header">Account</th>
              <th className="table-header">Created</th>
              <th className="table-header">Completed</th>
              <th className="table-header">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {jobs.length === 0 && (
              <tr>
                <td colSpan={6} className="table-cell text-center text-muted py-8">
                  <Wrench className="mx-auto mb-2" size={24} />
                  No jobs found.
                </td>
              </tr>
            )}
            {jobs.map((j) => (
              <tr key={j.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{j.type}</td>
                <td className="table-cell">
                  <span className={`badge ${statusBadge(j.status)}`}>{j.status}</span>
                </td>
                <td className="table-cell text-sm">{j.account_id}</td>
                <td className="table-cell text-sm">{new Date(j.created_at).toLocaleString()}</td>
                <td className="table-cell text-sm">{j.completed_at ? new Date(j.completed_at).toLocaleString() : "—"}</td>
                <td className="table-cell text-sm text-danger max-w-xs truncate">{j.error || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-sm text-muted">
        <div>
          Showing {jobs.length} of {total}
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <button className="btn-secondary text-xs" disabled={jobs.length < perPage} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
