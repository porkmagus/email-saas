import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { Loader2, Save, Trash2, Calendar } from "lucide-react";

interface VacationResponse {
  id: string;
  is_active: boolean;
  subject: string;
  body: string;
  start_at: string | null;
  end_at: string | null;
  only_contacts: boolean;
  only_aliases: boolean;
  updated_at: string;
}

export default function VacationResponsePage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<VacationResponse | null>(null);
  const [form, setForm] = useState({
    is_active: false,
    subject: "",
    body: "",
    start_at: "",
    end_at: "",
    only_contacts: false,
    only_aliases: false,
  });

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<VacationResponse | null>("/vacation-response");
      const vr = res.data;
      setData(vr);
      if (vr) {
        setForm({
          is_active: vr.is_active,
          subject: vr.subject || "",
          body: vr.body || "",
          start_at: vr.start_at ? vr.start_at.slice(0, 16) : "",
          end_at: vr.end_at ? vr.end_at.slice(0, 16) : "",
          only_contacts: vr.only_contacts,
          only_aliases: vr.only_aliases,
        });
      }
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put("/vacation-response", {
        ...form,
        start_at: form.start_at || null,
        end_at: form.end_at || null,
      });
      addToast("Vacation response saved", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Remove vacation response?")) return;
    try {
      await api.delete("/vacation-response");
      addToast("Vacation response removed", "success");
      setForm({ is_active: false, subject: "", body: "", start_at: "", end_at: "", only_contacts: false, only_aliases: false });
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to remove", "error");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Vacation response</h1>
        <p className="text-sm text-muted">Set up an automated out-of-office reply.</p>
      </div>

      <div className="card p-4 space-y-4">
        <form onSubmit={handleSave} className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            />
            <label htmlFor="is_active" className="text-sm font-medium">Enabled</label>
          </div>
          <div>
            <label className="label">Subject</label>
            <input
              className="input"
              value={form.subject}
              onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
              placeholder="Out of office"
            />
          </div>
          <div>
            <label className="label">Body</label>
            <textarea
              className="input"
              rows={6}
              value={form.body}
              onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
              placeholder="I am currently out of office..."
            />
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Start at</label>
              <input
                type="datetime-local"
                className="input"
                value={form.start_at}
                onChange={(e) => setForm((f) => ({ ...f, start_at: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">End at</label>
              <input
                type="datetime-local"
                className="input"
                value={form.end_at}
                onChange={(e) => setForm((f) => ({ ...f, end_at: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="only_contacts"
                checked={form.only_contacts}
                onChange={(e) => setForm((f) => ({ ...f, only_contacts: e.target.checked }))}
              />
              <label htmlFor="only_contacts" className="text-sm">Only reply to contacts</label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="only_aliases"
                checked={form.only_aliases}
                onChange={(e) => setForm((f) => ({ ...f, only_aliases: e.target.checked }))}
              />
              <label htmlFor="only_aliases" className="text-sm">Only reply to alias addresses</label>
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            {data && (
              <button type="button" className="btn-danger flex items-center gap-2" onClick={handleDelete}>
                <Trash2 size={16} />
                Delete
              </button>
            )}
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
