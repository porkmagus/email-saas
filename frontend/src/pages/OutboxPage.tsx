import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Send, Trash2, Loader2 } from "lucide-react";

interface OutboxItem {
  id: string;
  subject: string;
  recipient: string;
  status: "pending" | "sending" | "sent" | "failed" | "bounced";
  created_at: string;
  scheduled_at: string | null;
  sent_at: string | null;
}

export default function OutboxPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<OutboxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<OutboxItem[]>("/outbox");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load outbox", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Cancel this message?")) return;
    setDeleting(id);
    try {
      await api.delete(`/outbox/${id}`);
      addToast("Message cancelled", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to cancel", "error");
    } finally {
      setDeleting(null);
    }
  };

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: "bg-yellow-100 text-yellow-800",
      sending: "bg-blue-100 text-blue-800",
      sent: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
      bounced: "bg-orange-100 text-orange-800",
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${map[status] || "bg-gray-100 text-gray-800"}`}>
        {status}
      </span>
    );
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Outbox</h1>
          <p className="text-sm text-muted">Sent and scheduled messages.</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Subject</th>
              <th className="table-header">Recipient</th>
              <th className="table-header">Status</th>
              <th className="table-header">Created</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="table-cell text-center text-muted py-8">
                  <Send className="mx-auto mb-2" size={24} />
                  No messages in outbox.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{item.subject}</td>
                <td className="table-cell text-sm text-muted">{item.recipient}</td>
                <td className="table-cell">{statusBadge(item.status)}</td>
                <td className="table-cell text-sm text-muted">{new Date(item.created_at).toLocaleString()}</td>
                <td className="table-cell text-right">
                  <button
                    className="text-danger hover:opacity-80"
                    onClick={() => handleDelete(item.id)}
                    disabled={deleting === item.id}
                  >
                    {deleting === item.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
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
