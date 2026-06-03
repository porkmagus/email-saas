import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { ArrowLeft, Send, Shield, Loader2 } from "lucide-react";

interface TicketComment {
  id: string;
  author_id: string | null;
  author_email: string | null;
  is_internal: boolean;
  body: string;
  created_at: string;
}

interface Ticket {
  id: string;
  account_id: string;
  title: string;
  status: string;
  priority: string;
  category: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
  comments: TicketComment[];
}

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { account } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [isInternal, setIsInternal] = useState(false);
  const [updating, setUpdating] = useState(false);

  const isStaff = account?.role === "admin" || account?.role === "superadmin";

  const load = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get<Ticket>(`/tickets/${id}`);
      setTicket(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load ticket", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !reply.trim()) return;
    setSending(true);
    try {
      await api.post(`/tickets/${id}/comments`, { body: reply, is_internal: isInternal });
      addToast("Reply sent", "success");
      setReply("");
      setIsInternal(false);
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to send reply", "error");
    } finally {
      setSending(false);
    }
  };

  const handleStatusChange = async (status: string) => {
    if (!id) return;
    setUpdating(true);
    try {
      await api.patch(`/tickets/${id}`, { status });
      addToast("Status updated", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update status", "error");
    } finally {
      setUpdating(false);
    }
  };

  const statusOptions = () => {
    if (isStaff) return ["open", "waiting_customer", "waiting_staff", "resolved", "closed"];
    return ["resolved", "closed"];
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
  if (!ticket) return <div className="text-center text-muted py-12">Ticket not found.</div>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate("/tickets")} className="flex items-center gap-2 text-sm text-muted hover:text-primary">
        <ArrowLeft size={16} /> Back to tickets
      </button>

      <div className="card p-6">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <h1 className="text-xl font-bold">{ticket.title}</h1>
          <span className={`badge ${statusBadge(ticket.status)}`}>{ticket.status.replace("_", " ")}</span>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
          <span className="capitalize">{ticket.category}</span>
          <span>·</span>
          <span className="capitalize">{ticket.priority} priority</span>
          {isStaff && ticket.assigned_to && (
            <>
              <span>·</span>
              <span>Assigned: {ticket.assigned_to}</span>
            </>
          )}
        </div>
        {isStaff && (
          <div className="flex items-center gap-2 mt-4">
            <select
              className="input text-sm w-48"
              value={ticket.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              disabled={updating}
            >
              {statusOptions().map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
            {updating && <Loader2 size={16} className="animate-spin text-accent" />}
          </div>
        )}
      </div>

      <div className="space-y-3">
        {ticket.comments.length === 0 && (
          <div className="text-center text-sm text-muted py-4">No replies yet.</div>
        )}
        {ticket.comments.map((c) => (
          <div key={c.id} className={`card p-4 ${c.is_internal ? "border-l-4 border-l-accent" : ""}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">{c.author_email || "System"}</span>
                {c.is_internal && (
                  <span className="badge bg-accent/10 text-accent flex items-center gap-1">
                    <Shield size={10} /> Internal
                  </span>
                )}
              </div>
              <span className="text-xs text-muted">{new Date(c.created_at).toLocaleString()}</span>
            </div>
            <div className="text-sm whitespace-pre-wrap">{c.body}</div>
          </div>
        ))}
      </div>

      <div className="card p-4">
        <form onSubmit={handleReply} className="space-y-3">
          <textarea
            className="input min-h-[6rem]"
            placeholder="Write a reply..."
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            required
          />
          {isStaff && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="internal"
                className="rounded border-border"
                checked={isInternal}
                onChange={(e) => setIsInternal(e.target.checked)}
              />
              <label htmlFor="internal" className="text-sm text-muted">
                Internal note
              </label>
            </div>
          )}
          <div className="flex justify-end">
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={sending}>
              {sending ? <Loader2 size={16} className="animate-spin" /> : <>
                <Send size={16} /> Send
              </>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
