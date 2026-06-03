import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Trash2, Loader2, ShieldAlert, LogOut } from "lucide-react";

interface SessionItem {
  id: string;
  token_jti: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_active_at: string;
  expires_at: string;
}

export default function SessionsPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<SessionItem[]>("/sessions");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load sessions", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRevoke = async (id: string) => {
    if (!confirm("Revoke this session?")) return;
    setRevoking(id);
    try {
      await api.delete(`/sessions/${id}`);
      addToast("Session revoked", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to revoke", "error");
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAll = async () => {
    if (!confirm("Revoke ALL sessions? You will be logged out.")) return;
    setRevokingAll(true);
    try {
      await api.delete("/sessions");
      addToast("All sessions revoked. Please log in again.", "success");
      window.location.href = "/login";
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to revoke all", "error");
    } finally {
      setRevokingAll(false);
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Active sessions</h1>
          <p className="text-sm text-muted">Review and revoke sessions across devices.</p>
        </div>
        <button className="btn-danger flex items-center gap-2" onClick={handleRevokeAll} disabled={revokingAll}>
          {revokingAll ? <Loader2 size={16} className="animate-spin" /> : <LogOut size={16} />}
          Revoke all
        </button>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">IP address</th>
              <th className="table-header">User agent</th>
              <th className="table-header">Last active</th>
              <th className="table-header">Expires</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="table-cell text-center text-muted py-8">
                  <ShieldAlert className="mx-auto mb-2" size={24} />
                  No active sessions.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{item.ip_address || "—"}</td>
                <td className="table-cell text-sm text-muted truncate max-w-[200px]">
                  {item.user_agent || "—"}
                </td>
                <td className="table-cell text-sm text-muted">
                  {new Date(item.last_active_at).toLocaleString()}
                </td>
                <td className="table-cell text-sm text-muted">
                  {new Date(item.expires_at).toLocaleString()}
                </td>
                <td className="table-cell text-right">
                  <button
                    className="text-danger hover:opacity-80"
                    onClick={() => handleRevoke(item.id)}
                    disabled={revoking === item.id}
                  >
                    {revoking === item.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
