import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { LogIn, CheckCircle2, XCircle } from "lucide-react";

interface LoginLog {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  success: boolean;
  created_at: string;
}

export default function LoginLogsPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<LoginLog[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<LoginLog[]>("/login-logs");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load login logs", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Login history</h1>
        <p className="text-sm text-muted">Review recent sign-in attempts.</p>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Time</th>
              <th className="table-header">IP address</th>
              <th className="table-header">User agent</th>
              <th className="table-header">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="table-cell text-center text-muted py-8">
                  <LogIn className="mx-auto mb-2" size={24} />
                  No login history yet.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm text-muted">
                  {new Date(item.created_at).toLocaleString()}
                </td>
                <td className="table-cell text-sm font-medium">{item.ip_address || "—"}</td>
                <td className="table-cell text-sm text-muted truncate max-w-[200px]">
                  {item.user_agent || "—"}
                </td>
                <td className="table-cell">
                  {item.success ? (
                    <span className="inline-flex items-center gap-1 text-sm text-emerald-600">
                      <CheckCircle2 size={14} /> Success
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-sm text-danger">
                      <XCircle size={14} /> Failed
                    </span>
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
