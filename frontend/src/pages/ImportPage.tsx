import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Import,
  Server,
  Shield,
  CheckCircle,
  XCircle,
  Loader2,
  Database,
} from "lucide-react";

interface ImportJob {
  id: string;
  account_id: string;
  server: string;
  port: number;
  username: string;
  tls: boolean;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  messages_imported: number;
  errors: number;
  error_log: string | null;
  created_at: string;
  updated_at: string;
}

export default function ImportPage() {
  const { addToast } = useToast();
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    server: "",
    port: 993,
    username: "",
    password: "",
    tls: true,
    batch_size: 100,
  });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<ImportJob[]>("/import");
      setJobs(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load import jobs", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/import", {
        server: form.server,
        port: Number(form.port),
        username: form.username,
        password: form.password,
        tls: form.tls,
        batch_size: Number(form.batch_size),
      });
      addToast("Import job created", "success");
      setForm({ server: "", port: 993, username: "", password: "", tls: true, batch_size: 100 });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create import job", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle size={16} className="text-green-500" />;
      case "failed":
        return <XCircle size={16} className="text-red-500" />;
      case "running":
        return <Loader2 size={16} className="animate-spin text-accent" />;
      default:
        return <Loader2 size={16} className="text-muted" />;
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Import size={24} />
          Import
        </h1>
        <p className="text-sm text-muted">Import emails from an external IMAP server.</p>
      </div>

      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Server size={18} />
          New import job
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="label">Server</label>
            <input
              type="text"
              className="input"
              placeholder="imap.example.com"
              value={form.server}
              onChange={(e) => setForm({ ...form, server: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="label">Port</label>
            <input
              type="number"
              className="input"
              value={form.port}
              onChange={(e) => setForm({ ...form, port: Number(e.target.value) })}
              required
            />
          </div>
          <div>
            <label className="label">Username</label>
            <input
              type="text"
              className="input"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <div className="flex items-center gap-2 md:col-span-2">
            <input
              id="tls"
              type="checkbox"
              checked={form.tls}
              onChange={(e) => setForm({ ...form, tls: e.target.checked })}
            />
            <label htmlFor="tls" className="text-sm flex items-center gap-1">
              <Shield size={14} />
              Use TLS
            </label>
          </div>
          <div>
            <label className="label">Batch size</label>
            <input
              type="number"
              className="input"
              value={form.batch_size}
              onChange={(e) => setForm({ ...form, batch_size: Number(e.target.value) })}
              required
            />
          </div>
          <div className="md:col-span-2">
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={submitting}>
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <Import size={16} />}
              Start import
            </button>
          </div>
        </form>
      </div>

      <div className="card overflow-hidden">
        <h2 className="text-lg font-semibold px-4 py-3 border-b border-border flex items-center gap-2">
          <Database size={18} />
          Import jobs
        </h2>
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Status</th>
              <th className="table-header">Server</th>
              <th className="table-header">Username</th>
              <th className="table-header">Messages</th>
              <th className="table-header">Errors</th>
              <th className="table-header">Started</th>
              <th className="table-header">Completed</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {jobs.length === 0 && (
              <tr>
                <td colSpan={7} className="table-cell text-center text-muted py-8">
                  <Database className="mx-auto mb-2" size={24} />
                  No import jobs yet.
                </td>
              </tr>
            )}
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm flex items-center gap-1 capitalize">
                  {statusIcon(job.status)}
                  {job.status}
                </td>
                <td className="table-cell text-sm text-muted">{job.server}</td>
                <td className="table-cell text-sm text-muted">{job.username}</td>
                <td className="table-cell text-sm">{job.messages_imported}</td>
                <td className="table-cell text-sm">{job.errors}</td>
                <td className="table-cell text-sm text-muted">
                  {job.started_at ? new Date(job.started_at).toLocaleString() : "—"}
                </td>
                <td className="table-cell text-sm text-muted">
                  {job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
