import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { ArrowLeft, Send, Shield, Loader2, UserCheck } from "lucide-react";

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

interface CustomerCard {
  id: string;
  email: string;
  display_name: string | null;
  plan: string;
  status: string;
  domain_count: number;
  mailbox_count: number;
}

export default function AdminTicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isSuperadmin } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [customer, setCustomer] = useState<CustomerCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [isInternal, setIsInternal] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [assignee, setAssignee] = useState("");

  const load = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get<Ticket>(`/tickets/${id}`);
      setTicket(res.data);
      // Try to load customer info
      try {
        const cust = await api.get<CustomerCard>(`/admin/accounts/${res.data.account_id}`);
        setCustomer(cust.data);
      } catch {
        setCustomer(null);
      }
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

  const handleUpdate = async (patch: Partial<Ticket>) => {
    if (!id) return;
    setUpdating(true);
    try {
      await api.patch(`/tickets/${id}`, patch);
      addToast("Ticket updated", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update ticket", "error");
    } finally {
      setUpdating(false);
    }
  };

  const impersonate = async () => {
    if (!customer) return;
    try {
      const res = await api.get<{ token: string }>(`/admin/accounts/${customer.id}/impersonate`);
      const token = res.data.token;
      const url = `${window.location.origin}/dashboard?impersonate_token=${token}`;
      window.open(url, "_blank");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to impersonate", "error");
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
  if (!ticket) return <div className="text-center text-muted py-12">Ticket not found.</div>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate("/admin/tickets")} className="flex items-center gap-2 text-sm text-muted hover:text-primary">
        <ArrowLeft size={16} /> Back to queue
      </button>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
              <h1 className="text-xl font-bold">{ticket.title}</h1>
              <span className={`badge ${statusBadge(ticket.status)}`}>{ticket.status.replace("_", " ")}</span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
              <span className="capitalize">{ticket.category}</span>
              <span>·</span>
              <span className="capitalize">{ticket.priority} priority</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 mt-4">
              <select className="input text-sm w-40" value={ticket.status} onChange={(e) => handleUpdate({ status: e.target.value })} disabled={updating}>
                <option value="open">Open</option>
                <option value="waiting_customer">Waiting Customer</option>
                <option value="waiting_staff">Waiting Staff</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
              <select className="input text-sm w-40" value={ticket.priority} onChange={(e) => handleUpdate({ priority: e.target.value })} disabled={updating}>
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
              <input className="input text-sm w-48" placeholder="Assign to" value={assignee} onChange={(e) => setAssignee(e.target.value)} onBlur={() => handleUpdate({ assigned_to: assignee || null })} />
              {updating && <Loader2 size={16} className="animate-spin text-accent" />}
            </div>
          </div>

          <div className="space-y-3">
            {ticket.comments.length === 0 && <div className="text-center text-sm text-muted py-4">No replies yet.</div>}
            {ticket.comments.map((c) => (
              <div key={c.id} className={`card p-4 ${c.is_internal ? "border-l-4 border-l-accent" : ""}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">{c.author_email || "System"}</span>
                    {c.is_internal && <span className="badge bg-accent/10 text-accent flex items-center gap-1"><Shield size={10} /> Internal</span>}
                  </div>
                  <span className="text-xs text-muted">{new Date(c.created_at).toLocaleString()}</span>
                </div>
                <div className="text-sm whitespace-pre-wrap">{c.body}</div>
              </div>
            ))}
          </div>

          <div className="card p-4">
            <form onSubmit={handleReply} className="space-y-3">
              <textarea className="input min-h-[6rem]" placeholder="Write a reply..." value={reply} onChange={(e) => setReply(e.target.value)} required />
              <div className="flex items-center gap-2">
                <input type="checkbox" id="internal" className="rounded border-border" checked={isInternal} onChange={(e) => setIsInternal(e.target.checked)} />
                <label htmlFor="internal" className="text-sm text-muted">Internal note</label>
              </div>
              <div className="flex justify-end">
                <button type="submit" className="btn-primary flex items-center gap-2" disabled={sending}>
                  {sending ? <Loader2 size={16} className="animate-spin" /> : <><Send size={16} /> Send</>}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="font-semibold mb-4">Customer</h2>
            {customer ? (
              <div className="space-y-2 text-sm">
                <div><span className="text-muted">Email:</span> <span className="font-medium">{customer.email}</span></div>
                <div><span className="text-muted">Plan:</span> <span className="capitalize">{customer.plan}</span></div>
                <div><span className="text-muted">Status:</span> <span className="capitalize">{customer.status}</span></div>
                <div><span className="text-muted">Domains:</span> {customer.domain_count}</div>
                <div><span className="text-muted">Mailboxes:</span> {customer.mailbox_count}</div>
                {isSuperadmin && (
                  <button className="btn-secondary text-xs w-full mt-2 flex items-center justify-center gap-2" onClick={impersonate}>
                    <UserCheck size={14} /> Impersonate
                  </button>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted">Customer data unavailable.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
