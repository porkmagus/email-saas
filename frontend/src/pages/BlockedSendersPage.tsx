import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, Ban } from "lucide-react";

interface BlockedSender {
  id: string;
  email_or_domain: string;
  is_domain: boolean;
  created_at: string;
}

export default function BlockedSendersPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<BlockedSender[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email_or_domain: "" });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<BlockedSender[]>("/blocked-senders");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load list", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/blocked-senders", form);
      addToast("Blocked sender added", "success");
      setShowForm(false);
      setForm({ email_or_domain: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to add", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this entry?")) return;
    try {
      await api.delete(`/blocked-senders/${id}`);
      addToast("Removed", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to remove", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Blocked senders</h1>
          <p className="text-sm text-muted">Block emails or entire domains.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add entry"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="label">Email or domain</label>
              <input
                type="text"
                className="input"
                placeholder="spam@example.com or @example.com"
                value={form.email_or_domain}
                onChange={(e) => setForm({ email_or_domain: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
              {creating ? <Loader2 size={16} className="animate-spin" /> : "Block"}
            </button>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Blocked address</th>
              <th className="table-header">Type</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={3} className="table-cell text-center text-muted py-8">
                  <Ban className="mx-auto mb-2" size={24} />
                  No blocked entries yet.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{item.email_or_domain}</td>
                <td className="table-cell">
                  <span className={`badge ${item.is_domain ? "badge-warning" : "badge-danger"}`}>
                    {item.is_domain ? "Domain" : "Email"}
                  </span>
                </td>
                <td className="table-cell text-right">
                  <button className="text-danger hover:opacity-80" onClick={() => handleDelete(item.id)}>
                    <Trash2 size={16} />
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
