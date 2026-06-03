import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, Moon } from "lucide-react";

interface Snooze {
  id: string;
  subject_contains: string | null;
  sender_address: string | null;
  until: string;
  active: boolean;
  created_at: string;
}

export default function SnoozePage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<Snooze[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    subject_contains: "",
    sender_address: "",
    until: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Snooze[]>("/snooze");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load snooze rules", "error");
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
      const payload: any = {
        until: new Date(form.until).toISOString(),
      };
      if (form.subject_contains.trim()) payload.subject_contains = form.subject_contains.trim();
      if (form.sender_address.trim()) payload.sender_address = form.sender_address.trim();
      await api.post("/snooze", payload);
      addToast("Snooze rule created", "success");
      setShowForm(false);
      setForm({ subject_contains: "", sender_address: "", until: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this snooze rule?")) return;
    try {
      await api.delete(`/snooze/${id}`);
      addToast("Deleted", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete", "error");
    }
  };

  const handleEnd = async (id: string) => {
    try {
      await api.post(`/snooze/${id}/end`);
      addToast("Snooze ended", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to end", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Snooze</h1>
          <p className="text-sm text-muted">Hold emails matching criteria until a date.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add snooze rule"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="space-y-3">
            <div>
              <label className="label">Subject contains</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., invoice"
                value={form.subject_contains}
                onChange={(e) => setForm({ ...form, subject_contains: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Sender address</label>
              <input
                type="email"
                className="input"
                placeholder="e.g., noreply@example.com"
                value={form.sender_address}
                onChange={(e) => setForm({ ...form, sender_address: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Snooze until</label>
              <input
                type="datetime-local"
                className="input"
                value={form.until}
                onChange={(e) => setForm({ ...form, until: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
              {creating ? <Loader2 size={16} className="animate-spin" /> : "Create"}
            </button>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Subject contains</th>
              <th className="table-header">Sender address</th>
              <th className="table-header">Until</th>
              <th className="table-header">Status</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="table-cell text-center text-muted py-8">
                  <Moon className="mx-auto mb-2" size={24} />
                  No snooze rules yet.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm">{item.subject_contains || "—"}</td>
                <td className="table-cell text-sm text-muted">{item.sender_address || "—"}</td>
                <td className="table-cell text-sm text-muted">{new Date(item.until).toLocaleString()}</td>
                <td className="table-cell">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      item.active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {item.active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="table-cell text-right space-x-2">
                  {item.active && (
                    <button className="text-sm text-primary hover:underline" onClick={() => handleEnd(item.id)}>
                      End
                    </button>
                  )}
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
