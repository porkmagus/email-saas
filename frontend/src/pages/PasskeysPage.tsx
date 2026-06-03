import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, Fingerprint } from "lucide-react";

interface Passkey {
  id: string;
  name: string;
  credential_id: string;
  created_at: string;
}

export default function PasskeysPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<Passkey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "" });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Passkey[]>("/passkeys");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load passkeys", "error");
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
      await api.post("/passkeys", form);
      addToast("Passkey registered", "success");
      setShowForm(false);
      setForm({ name: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to register", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this passkey?")) return;
    try {
      await api.delete(`/passkeys/${id}`);
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
          <h1 className="text-2xl font-bold">Passkeys</h1>
          <p className="text-sm text-muted">Manage your WebAuthn passkeys.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add passkey"}
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
                placeholder="e.g., MacBook Touch ID"
                value={form.name}
                onChange={(e) => setForm({ name: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
              {creating ? <Loader2 size={16} className="animate-spin" /> : "Register"}
            </button>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Name</th>
              <th className="table-header">Credential ID</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={3} className="table-cell text-center text-muted py-8">
                  <Fingerprint className="mx-auto mb-2" size={24} />
                  No passkeys registered.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{item.name}</td>
                <td className="table-cell text-sm text-muted font-mono truncate max-w-[200px]">
                  {item.credential_id}
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
