import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Plus, Trash2, Loader2, FileText } from "lucide-react";

interface FileItem {
  id: string;
  name: string;
  path: string;
  size_bytes: number;
  mime_type: string | null;
  folder: string | null;
  created_at: string;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export default function FilesPage() {
  const { addToast } = useToast();
  const [items, setItems] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", path: "", size_bytes: 0, mime_type: "", folder: "" });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<FileItem[]>("/files");
      setItems(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load files", "error");
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
      const payload: any = { name: form.name, path: form.path, size_bytes: form.size_bytes || 0 };
      if (form.mime_type) payload.mime_type = form.mime_type;
      if (form.folder) payload.folder = form.folder;
      await api.post("/files", payload);
      addToast("File entry added", "success");
      setShowForm(false);
      setForm({ name: "", path: "", size_bytes: 0, mime_type: "", folder: "" });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to add", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this file entry?")) return;
    try {
      await api.delete(`/files/${id}`);
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
          <h1 className="text-2xl font-bold">Files</h1>
          <p className="text-sm text-muted">Manage your file entries.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "Add file"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Name</label>
                <input
                  type="text"
                  className="input"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="label">Path</label>
                <input
                  type="text"
                  className="input"
                  value={form.path}
                  onChange={(e) => setForm({ ...form, path: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="label">Size (bytes)</label>
                <input
                  type="number"
                  className="input"
                  value={form.size_bytes}
                  onChange={(e) => setForm({ ...form, size_bytes: Number(e.target.value) })}
                />
              </div>
              <div>
                <label className="label">Folder</label>
                <input
                  type="text"
                  className="input"
                  value={form.folder}
                  onChange={(e) => setForm({ ...form, folder: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="label">MIME type</label>
              <input
                type="text"
                className="input"
                value={form.mime_type}
                onChange={(e) => setForm({ ...form, mime_type: e.target.value })}
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
              {creating ? <Loader2 size={16} className="animate-spin" /> : "Add"}
            </button>
          </form>
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-alt border-b border-border">
            <tr>
              <th className="table-header">Name</th>
              <th className="table-header">Folder</th>
              <th className="table-header">Size</th>
              <th className="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="table-cell text-center text-muted py-8">
                  <FileText className="mx-auto mb-2" size={24} />
                  No files yet.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-surface-alt/50">
                <td className="table-cell text-sm font-medium">{item.name}</td>
                <td className="table-cell text-sm text-muted">{item.folder || "—"}</td>
                <td className="table-cell text-sm text-muted">{formatBytes(item.size_bytes)}</td>
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
