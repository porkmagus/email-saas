import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, AtSign, Check, X } from "lucide-react";

interface Alias {
  id: string;
  source: string;
  destination_local_part: string;
  destination_domain_id: string;
  domain_id: string;
  status: string;
  created_at: string;
  domain?: string;
  destination_domain?: string;
}

interface DomainOption {
  id: string;
  domain: string;
}

export default function AliasesPage() {
  const { addToast } = useToast();
  const [aliases, setAliases] = useState<Alias[]>([]);
  const [domains, setDomains] = useState<DomainOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    source: "",
    destination_local_part: "",
    destination_domain_id: "",
    domain_id: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      const [aRes, dRes] = await Promise.all([
        api.get<Alias[]>("/aliases"),
        api.get<DomainOption[]>("/domains"),
      ]);
      setAliases(aRes.data);
      setDomains(dRes.data.map((d) => ({ id: d.id, domain: d.domain })));
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load aliases", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.domain_id || !form.destination_domain_id) {
      addToast("Select both domains", "warning");
      return;
    }
    setCreating(true);
    try {
      await api.post("/aliases", form);
      addToast("Alias created", "success");
      setShowForm(false);
      setForm({ source: "", destination_local_part: "", destination_domain_id: "", domain_id: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create alias", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this alias?")) return;
    try {
      await api.delete(`/aliases/${id}`);
      addToast("Alias deleted", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete alias", "error");
    }
  };

  const handleToggle = async (id: string, current: string) => {
    const newStatus = current === "active" ? "paused" : "active";
    try {
      await api.patch(`/aliases/${id}`, { status: newStatus });
      addToast(`Alias ${newStatus}`, "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update alias", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Aliases</h1>
          <p className="text-sm text-muted">Create and manage email aliases.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add alias"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Source alias</label>
              <input
                type="text"
                className="input"
                placeholder="support@yourdomain.com"
                value={form.source}
                onChange={(e) => setForm((f) => ({ ...f, source: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="label">Destination mailbox</label>
              <input
                type="text"
                className="input"
                placeholder="john"
                value={form.destination_local_part}
                onChange={(e) => setForm((f) => ({ ...f, destination_local_part: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="label">Alias domain</label>
              <select
                className="input"
                value={form.domain_id}
                onChange={(e) => setForm((f) => ({ ...f, domain_id: e.target.value }))}
                required
              >
                <option value="">Select domain</option>
                {domains.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.domain}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Destination domain</label>
              <select
                className="input"
                value={form.destination_domain_id}
                onChange={(e) => setForm((f) => ({ ...f, destination_domain_id: e.target.value }))}
                required
              >
                <option value="">Select domain</option>
                {domains.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.domain}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
                {creating ? <Loader2 size={16} className="animate-spin" /> : "Create alias"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Source</th>
              <th className="table-header">Destination</th>
              <th className="table-header">Status</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {aliases.length === 0 && (
              <tr>
                <td colSpan={4} className="table-cell text-center text-muted py-8">
                  <AtSign className="mx-auto mb-2" size={24} />
                  No aliases yet.
                </td>
              </tr>
            )}
            {aliases.map((a) => (
              <tr key={a.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{a.source}</td>
                <td className="table-cell text-sm text-muted">
                  {a.destination_local_part}@{a.destination_domain || a.destination_domain_id}
                </td>
                <td className="table-cell">
                  <span className={`badge ${a.status === "active" ? "badge-success" : "badge-warning"}`}>{a.status}</span>
                </td>
                <td className="table-cell text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      className="text-muted hover:text-primary"
                      title={a.status === "active" ? "Pause" : "Activate"}
                      onClick={() => handleToggle(a.id, a.status)}
                    >
                      {a.status === "active" ? <X size={16} /> : <Check size={16} />}
                    </button>
                    <button className="text-danger hover:opacity-80" onClick={() => handleDelete(a.id)}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
