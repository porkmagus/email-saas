import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, Save, StickyNote } from "lucide-react";

interface Note {
  id: string;
  title: string;
  content: string | null;
  created_at: string;
  updated_at: string;
}

export default function NotesPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", content: "" });
  const [editing, setEditing] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ title: "", content: "" });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Note[]>("/notes");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load notes", "error");
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
      const payload: any = { title: form.title };
      if (form.content) payload.content = form.content;
      await api.post("/notes", payload);
      addToast("Note created", "success");
      setShowForm(false);
      setForm({ title: "", content: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this note?")) return;
    try {
      await api.delete(`/notes/${id}`);
      addToast("Deleted", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete", "error");
    }
  };

  const startEdit = (note: Note) => {
    setEditing(note.id);
    setEditForm({ title: note.title, content: note.content || "" });
  };

  const handleUpdate = async (id: string) => {
    try {
      const payload: any = {};
      if (editForm.title) payload.title = editForm.title;
      if (editForm.content) payload.content = editForm.content;
      await api.patch(`/notes/${id}`, payload);
      addToast("Note updated", "success");
      setEditing(null);
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Notes</h1>
          <p className="text-sm text-muted">Keep your ideas and reminders here.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add note"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="space-y-3">
            <div>
              <label className="label">Title</label>
              <input
                type="text"
                className="input"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Content</label>
              <textarea
                className="input min-h-[80px]"
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
              {creating ? <Loader2 size={16} className="animate-spin" /> : "Create"}
            </button>
          </form>
        </div>
      )}

      <div className="space-y-3">
        {items.length === 0 && (
          <div className="card p-8 text-center text-muted">
            <StickyNote className="mx-auto mb-2" size={24} />
            No notes yet.
          </div>
        )}
        {items.map((note) => (
          <div key={note.id} className="card p-4">
            {editing === note.id ? (
              <div className="space-y-3">
                <input
                  type="text"
                  className="input"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                />
                <textarea
                  className="input min-h-[80px]"
                  value={editForm.content}
                  onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                />
                <div className="flex gap-2">
                  <button className="btn-primary flex items-center gap-2" onClick={() => handleUpdate(note.id)}>
                    <Save size={16} /> Save
                  </button>
                  <button className="btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{note.title}</h3>
                  <div className="flex items-center gap-2">
                    <button className="text-sm text-muted hover:text-primary" onClick={() => startEdit(note)}>
                      Edit
                    </button>
                    <button className="text-danger hover:opacity-80" onClick={() => handleDelete(note.id)}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                {note.content && <p className="text-sm text-muted whitespace-pre-wrap">{note.content}</p>}
                <p className="text-xs text-muted">Updated {new Date(note.updated_at).toLocaleString()}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
