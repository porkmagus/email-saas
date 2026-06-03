import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/Loading";
import { Link } from "react-router-dom";
import { HelpCircle, Plus, Loader2 } from "lucide-react";

interface Ticket {
  id: string;
  title: string;
  status: string;
  priority: string;
  category: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export default function TicketsPage() {
  const { account } = useAuth();
  const { addToast } = useToast();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState("other");

  const isStaff = account?.role === "admin" || account?.role === "superadmin";

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ items: Ticket[] }>("/tickets");
      setTickets(res.data.items);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load tickets", "error");
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
      await api.post("/tickets", { title, body, category });
      addToast("Ticket created", "success");
      setShowForm(false);
      setTitle("");
      setBody("");
      setCategory("other");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create ticket", "error");
    } finally {
      setCreating(false);
    }
  };

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      open: "badge-warning",
      waiting_customer: "badge-muted",
      waiting_staff: "badge-accent",
      resolved: "badge-success",
      closed: "badge-muted",
    };
    return map[status] || "badge-muted";
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Support</h1>
          <p className="text-sm text-muted">Get help from our team.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          {showForm ? "Close" : "New ticket"}
        </button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="label">Title</label>
              <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={500} />
            </div>
            <div>
              <label className="label">Category</label>
              <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="billing">Billing</option>
                <option value="setup">Setup</option>
                <option value="delivery">Delivery</option>
                <option value="account">Account</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="label">Description</label>
              <textarea className="input min-h-[6rem]" value={body} onChange={(e) => setBody(e.target.value)} required />
            </div>
            <div className="flex justify-end">
              <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
                {creating ? <Loader2 size={16} className="animate-spin" /> : "Submit ticket"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-2">
        {tickets.length === 0 && (
          <div className="card p-8 text-center">
            <HelpCircle className="mx-auto text-muted mb-2" size={32} />
            <p className="text-sm text-muted">No tickets yet. Create one if you need help.</p>
          </div>
        )}
        {tickets.map((t) => (
          <Link key={t.id} to={`/tickets/${t.id}`} className="card p-4 block hover:bg-surface-alt transition-colors">
            <div className="flex items-center justify-between">
              <div className="font-medium text-sm">{t.title}</div>
              <span className={`badge ${statusBadge(t.status)}`}>{t.status.replace("_", " ")}</span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs text-muted">
              <span className="capitalize">{t.category}</span>
              <span>·</span>
              <span className="capitalize">{t.priority} priority</span>
              {isStaff && t.assigned_to && (
                <>
                  <span>·</span>
                  <span>Assigned to {t.assigned_to}</span>
                </>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
