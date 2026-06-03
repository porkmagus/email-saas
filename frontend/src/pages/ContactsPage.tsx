import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, Pencil, Check, X, Star, StarOff, BookUser } from "lucide-react";

interface Contact {
  id: string;
  email: string;
  display_name: string | null;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  notes: string | null;
  is_vip: boolean;
  created_at: string;
}

export default function ContactsPage() {
  const { addToast } = useToast();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    email: "",
    display_name: "",
    first_name: "",
    last_name: "",
    phone: "",
    notes: "",
    is_vip: false,
  });

  const [editForm, setEditForm] = useState({
    display_name: "",
    first_name: "",
    last_name: "",
    phone: "",
    notes: "",
    is_vip: false,
  });

  const load = async () => {
    setLoading(true);
    try {
      const cRes = await api.get<Contact[]>("/contacts");
      setContacts(cRes.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load contacts", "error");
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
      await api.post("/contacts", form);
      addToast("Contact added", "success");
      setShowForm(false);
      setForm({ email: "", display_name: "", first_name: "", last_name: "", phone: "", notes: "", is_vip: false });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to add contact", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this contact?")) return;
    try {
      await api.delete(`/contacts/${id}`);
      addToast("Contact deleted", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete contact", "error");
    }
  };

  const handleEdit = (c: Contact) => {
    setEditingId(c.id);
    setEditForm({
      display_name: c.display_name || "",
      first_name: c.first_name || "",
      last_name: c.last_name || "",
      phone: c.phone || "",
      notes: c.notes || "",
      is_vip: c.is_vip,
    });
  };

  const handleSaveEdit = async (id: string) => {
    try {
      await api.patch(`/contacts/${id}`, editForm);
      addToast("Contact updated", "success");
      setEditingId(null);
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update contact", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Contacts</h1>
          <p className="text-sm text-muted">Manage your address book.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add contact"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Email</label>
              <input type="email" className="input" required value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </div>
            <div>
              <label className="label">Display name</label>
              <input type="text" className="input" value={form.display_name} onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">First name</label>
              <input type="text" className="input" value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Last name</label>
              <input type="text" className="input" value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Phone</label>
              <input type="text" className="input" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input type="checkbox" id="is_vip" checked={form.is_vip} onChange={(e) => setForm((f) => ({ ...f, is_vip: e.target.checked }))} />
              <label htmlFor="is_vip" className="text-sm font-medium">VIP</label>
            </div>
            <div className="sm:col-span-2">
              <label className="label">Notes</label>
              <textarea className="input" rows={2} value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
                {creating ? <Loader2 size={16} className="animate-spin" /> : "Add contact"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Contact</th>
              <th className="table-header">Phone</th>
              <th className="table-header">Notes</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {contacts.length === 0 && (
              <tr>
                <td colSpan={4} className="table-cell text-center text-muted py-8">
                  <BookUser className="mx-auto mb-2" size={24} />
                  No contacts yet.
                </td>
              </tr>
            )}
            {contacts.map((c) => (
              <tr key={c.id} className="hover:bg-surface-alt/50">
                {editingId === c.id ? (
                  <>
                    <td className="table-cell">
                      <div className="flex items-center gap-2 mb-1">
                        <button
                          className="text-muted hover:text-warning"
                          onClick={() => setEditForm((f) => ({ ...f, is_vip: !f.is_vip }))}
                          title="Toggle VIP"
                        >
                          {editForm.is_vip ? <Star size={14} className="text-warning fill-warning" /> : <StarOff size={14} />}
                        </button>
                        <span className="text-sm font-medium">{c.email}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <input className="input text-sm" placeholder="Display name" value={editForm.display_name} onChange={(e) => setEditForm((f) => ({ ...f, display_name: e.target.value }))} />
                        <input className="input text-sm" placeholder="Phone" value={editForm.phone} onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))} />
                        <input className="input text-sm" placeholder="First name" value={editForm.first_name} onChange={(e) => setEditForm((f) => ({ ...f, first_name: e.target.value }))} />
                        <input className="input text-sm" placeholder="Last name" value={editForm.last_name} onChange={(e) => setEditForm((f) => ({ ...f, last_name: e.target.value }))} />
                        <textarea className="input text-sm col-span-2" rows={2} placeholder="Notes" value={editForm.notes} onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))} />
                      </div>
                    </td>
                    <td className="table-cell text-sm text-muted">{c.phone || "—"}</td>
                    <td className="table-cell text-sm text-muted max-w-xs truncate">{c.notes || "—"}</td>
                    <td className="table-cell text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="text-success hover:opacity-80" onClick={() => handleSaveEdit(c.id)}>
                          <Check size={16} />
                        </button>
                        <button className="text-muted hover:text-primary" onClick={() => setEditingId(null)}>
                          <X size={16} />
                        </button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <button
                          className="text-muted hover:text-warning"
                          onClick={async () => {
                            try {
                              await api.patch(`/contacts/${c.id}`, { is_vip: !c.is_vip });
                              addToast(c.is_vip ? "VIP removed" : "Marked VIP", "success");
                              await load();
                            } catch (err: any) {
                              addToast(err?.response?.data?.detail || "Failed to update", "error");
                            }
                          }}
                          title="Toggle VIP"
                        >
                          {c.is_vip ? <Star size={14} className="text-warning fill-warning" /> : <StarOff size={14} />}
                        </button>
                        <div>
                          <div className="font-medium text-sm">
                            {c.display_name || `${c.first_name || ""} ${c.last_name || ""}`.trim() || c.email}
                          </div>
                          <div className="text-xs text-muted">{c.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="table-cell text-sm text-muted">{c.phone || "—"}</td>
                    <td className="table-cell text-sm text-muted max-w-xs truncate">{c.notes || "—"}</td>
                    <td className="table-cell text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="text-muted hover:text-primary" onClick={() => handleEdit(c)}>
                          <Pencil size={16} />
                        </button>
                        <button className="text-danger hover:opacity-80" onClick={() => handleDelete(c.id)}>
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
