import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Mail, Plus, Trash2, Loader2, Pencil, Check, X } from "lucide-react";

interface Mailbox {
  id: string;
  local_part: string;
  display_name: string | null;
  quota_bytes: number;
  domain_id: string;
  domain: string | null;
  status: string;
  created_at: string;
}

interface DomainOption {
  id: string;
  domain: string;
}

export default function MailboxesPage() {
  const { addToast } = useToast();
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [domains, setDomains] = useState<DomainOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    local_part: "",
    display_name: "",
    password: "",
    domain_id: "",
    quota_bytes: 1073741824,
  });

  const [editForm, setEditForm] = useState({
    display_name: "",
    quota_bytes: 1073741824,
    password: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      const [mbRes, domRes] = await Promise.all([
        api.get<Mailbox[]>("/mailboxes"),
        api.get<{ id: string; domain: string }[]>("/domains"),
      ]);
      setMailboxes(mbRes.data);
      setDomains(domRes.data.map((d) => ({ id: d.id, domain: d.domain })));
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load mailboxes", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.domain_id) {
      addToast("Select a domain", "warning");
      return;
    }
    setCreating(true);
    try {
      await api.post("/mailboxes", {
        local_part: form.local_part,
        display_name: form.display_name || null,
        password: form.password,
        domain_id: form.domain_id,
        quota_bytes: Number(form.quota_bytes),
      });
      addToast("Mailbox created", "success");
      setShowForm(false);
      setForm({ local_part: "", display_name: "", password: "", domain_id: "", quota_bytes: 1073741824 });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create mailbox", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this mailbox?")) return;
    try {
      await api.delete(`/mailboxes/${id}`);
      addToast("Mailbox queued for deletion", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete mailbox", "error");
    }
  };

  const handleEdit = (mb: Mailbox) => {
    setEditingId(mb.id);
    setEditForm({
      display_name: mb.display_name || "",
      quota_bytes: mb.quota_bytes,
      password: "",
    });
  };

  const handleSaveEdit = async (id: string) => {
    try {
      await api.patch(`/mailboxes/${id}`, {
        display_name: editForm.display_name || null,
        quota_bytes: Number(editForm.quota_bytes),
        password: editForm.password || undefined,
      });
      addToast("Mailbox updated", "success");
      setEditingId(null);
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update mailbox", "error");
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Mailboxes</h1>
          <p className="text-sm text-muted">Create and manage mailboxes for your domains.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add mailbox"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Domain</label>
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
              <label className="label">Local part</label>
              <input
                type="text"
                className="input"
                placeholder="hello"
                value={form.local_part}
                onChange={(e) => setForm((f) => ({ ...f, local_part: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="label">Display name</label>
              <input
                type="text"
                className="input"
                placeholder="Support Team"
                value={form.display_name}
                onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                className="input"
                placeholder="Min 8 characters"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                required
                minLength={8}
              />
            </div>
            <div>
              <label className="label">Quota (bytes)</label>
              <input
                type="number"
                className="input"
                value={form.quota_bytes}
                onChange={(e) => setForm((f) => ({ ...f, quota_bytes: Number(e.target.value) }))}
                min={0}
              />
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
                {creating ? <Loader2 size={16} className="animate-spin" /> : "Create mailbox"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Mailbox</th>
              <th className="table-header">Domain</th>
              <th className="table-header">Quota</th>
              <th className="table-header">Status</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {mailboxes.length === 0 && (
              <tr>
                <td colSpan={5} className="table-cell text-center text-muted py-8">
                  <Mail className="mx-auto mb-2" size={24} />
                  No mailboxes yet.
                </td>
              </tr>
            )}
            {mailboxes.map((mb) => (
              <tr key={mb.id} className="hover:bg-surface-alt/50">
                <td className="table-cell">
                  {editingId === mb.id ? (
                    <input
                      className="input text-sm"
                      value={editForm.display_name}
                      onChange={(e) => setEditForm((f) => ({ ...f, display_name: e.target.value }))}
                      placeholder="Display name"
                    />
                  ) : (
                    <div>
                      <div className="font-medium text-sm">{mb.local_part}</div>
                      <div className="text-xs text-muted">{mb.display_name || "—"}</div>
                    </div>
                  )}
                </td>
                <td className="table-cell text-sm">{mb.domain || mb.domain_id}</td>
                <td className="table-cell text-sm">
                  {editingId === mb.id ? (
                    <input
                      className="input text-sm w-32"
                      type="number"
                      value={editForm.quota_bytes}
                      onChange={(e) => setEditForm((f) => ({ ...f, quota_bytes: Number(e.target.value) }))}
                    />
                  ) : (
                    formatBytes(mb.quota_bytes)
                  )}
                </td>
                <td className="table-cell">
                  <span className={`badge ${mb.status === "active" ? "badge-success" : "badge-danger"}`}>{mb.status}</span>
                </td>
                <td className="table-cell text-right">
                  {editingId === mb.id ? (
                    <div className="flex items-center justify-end gap-2">
                      <button className="text-success hover:opacity-80" onClick={() => handleSaveEdit(mb.id)}>
                        <Check size={16} />
                      </button>
                      <button className="text-danger hover:opacity-80" onClick={() => setEditingId(null)}>
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-end gap-2">
                      <button className="text-muted hover:text-primary" onClick={() => handleEdit(mb)}>
                        <Pencil size={16} />
                      </button>
                      <button className="text-danger hover:opacity-80" onClick={() => handleDelete(mb.id)}>
                        <Trash2 size={16} />
                      </button>
                    </div>
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
