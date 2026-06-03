import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Download,
  FileText,
  Calendar,
  Users,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";

interface ExportJob {
  id: string;
  account_id: string;
  type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  file_path: string | null;
  file_size: number | null;
  created_at: string;
  updated_at: string;
}

export default function ExportPage() {
  const { addToast } = useToast();
  const [jobs, setJobs] = useState<ExportJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<ExportJob[]>("/export");
      setJobs(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load export jobs", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleExport = async (type: string) => {
    setExporting(type);
    try {
      await api.post(`/export/${type}`, {});
      addToast(`${type} export started`, "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || `Failed to start ${type} export`, "error");
    } finally {
      setExporting(null);
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

  const formatBytes = (bytes: number | null) => {
    if (bytes == null) return "—";
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Download size={24} />
          Export
        </h1>
        <p className="text-sm text-muted">Export your emails, calendar, or contacts.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2">
            <FileText size={20} className="text-accent" />
            <h2 className="text-lg font-semibold">Export Emails</h2>
          </div>
          <p className="text-sm text-muted">Download your emails as an MBOX archive.</p>
          <button
            className="btn-primary w-full flex items-center justify-center gap-2"
            disabled={exporting === "emails"}
            onClick={() => handleExport("emails")}
          >
            {exporting === "emails" ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Export
          </button>
        </div>

        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Calendar size={20} className="text-accent" />
            <h2 className="text-lg font-semibold">Export Calendar</h2>
          </div>
          <p className="text-sm text-muted">Download your calendar events as an ICS file.</p>
          <button
            className="btn-primary w-full flex items-center justify-center gap-2"
            disabled={exporting === "calendar"}
            onClick={() => handleExport("calendar")}
          >
            {exporting === "calendar" ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Export
          </button>
        </div>

        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Users size={20} className="text-accent" />
            <h2 className="text-lg font-semibold">Export Contacts</h2>
          </div>
          <p className="text-sm text-muted">Download your contacts as a vCard file.</p>
          <button
            className="btn-primary w-full flex items-center justify-center gap-2"
            disabled={exporting === "contacts"}
            onClick={() => handleExport("contacts")}
          >
            {exporting === "contacts" ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Export
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <h2 className="text-lg font-semibold px-4 py-3 border-b border-border flex items-center gap-2">
          <Download size={18} />
          Recent exports
        </h2>
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Status</th>
              <th className="table-header">Type</th>
              <th className="table-header">File size</th>
              <th className="table-header">Started</th>
              <th className="table-header">Completed</th>
              <th className="table-header">Download</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {jobs.length === 0 && (
              <tr>
                <td colSpan={6} className="table-cell text-center text-muted py-8">
                  <Download className="mx-auto mb-2" size={24} />
                  No export jobs yet.
                </td>
              </tr>
            )}
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm flex items-center gap-1 capitalize">
                  {statusIcon(job.status)}
                  {job.status}
                </td>
                <td className="table-cell text-sm capitalize">{job.type}</td>
                <td className="table-cell text-sm">{formatBytes(job.file_size)}</td>
                <td className="table-cell text-sm text-muted">
                  {job.started_at ? new Date(job.started_at).toLocaleString() : "—"}
                </td>
                <td className="table-cell text-sm text-muted">
                  {job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"}
                </td>
                <td className="table-cell text-sm">
                  {job.status === "completed" && job.file_path ? (
                    <a
                      href="#"
                      className="text-primary hover:underline flex items-center gap-1"
                      onClick={(e) => {
                        e.preventDefault();
                        addToast("Download link placeholder", "info");
                      }}
                    >
                      <Download size={14} />
                      Download
                    </a>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
