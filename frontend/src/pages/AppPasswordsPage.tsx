import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, KeyRound } from "lucide-react";

interface AppPassword {
  id: string;
  name: string;
  permissions: string[];
  created_at: string;
}

export default function AppPasswordsPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<AppPassword[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", permissions: "" });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<AppPassword[]>("/app-passwords");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load app passwords", "error");
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
      const perms = form.permissions
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      await api.post("/app-passwords", { name: form.name, permissions: perms });
      addToast("App password created", "success");
      setShowForm(false);
      setForm({ name: "", permissions: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this app password?")) return;
    try {
      await api.delete(`/app-passwords/${id}`);
      addToast("Deleted", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">App passwords</h1>
          <p className="text-sm text-muted">Generate passwords for apps and devices.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add app password"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="space-y-3">
            <div>
              <label className="label">Name</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., Thunderbird"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Permissions (comma-separated)</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., mail, imap, smtp"
                value={form.permissions}
                onChange={(e) => setForm({ ...form, permissions: e.target.value })}
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
              <th className="table-header">Name</th>
              <th className="table-header">Permissions</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={3} className="table-cell text-center text-muted py-8">
                  <KeyRound className="mx-auto mb-2" size={24} />
                  No app passwords yet.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{item.name}</td>
                <td className="table-cell text-sm text-muted">{item.permissions.join(", ")}</td>
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
