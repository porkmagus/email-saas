import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import Loading from "../../components/Loading";
import { ArrowLeft, UserCheck, UserX, Loader2 } from "lucide-react";

interface Customer {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  status: string;
  plan: string;
  totp_enabled: boolean;
  created_at: string;
  updated_at: string;
  stripe_customer_id: string | null;
  domain_count: number;
  mailbox_count: number;
  subscription_status: string | null;
}

export default function AdminCustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isSuperadmin } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get<Customer>(`/admin/accounts/${id}`);
      setCustomer(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load customer", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const suspend = async () => {
    if (!id) return;
    const reason = prompt("Suspension reason:");
    if (!reason) return;
    setActionLoading(true);
    try {
      await api.post(`/admin/accounts/${id}/suspend`, { reason });
      addToast("Account suspended", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to suspend", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const unsuspend = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.post(`/admin/accounts/${id}/unsuspend`);
      addToast("Account unsuspended", "success");
      await load();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to unsuspend", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const impersonate = async () => {
    if (!id) return;
    try {
      const res = await api.get<{ token: string }>(`/admin/accounts/${id}/impersonate`);
      const token = res.data.token;
      const url = `${window.location.origin}/dashboard?impersonate_token=${token}`;
      window.open(url, "_blank");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to impersonate", "error");
    }
  };

  if (loading) return <Loading />;
  if (!customer) return <div className="text-center text-muted py-12">Customer not found.</div>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate("/admin/customers")} className="flex items-center gap-2 text-sm text-muted hover:text-primary">
        <ArrowLeft size={16} /> Back to customers
      </button>

      <div className="card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h1 className="text-xl font-bold">{customer.email}</h1>
            <p className="text-sm text-muted">{customer.display_name || "No display name"}</p>
          </div>
          <div className="flex items-center gap-2">
            {isSuperadmin && (
              <button className="btn-secondary text-sm flex items-center gap-2" onClick={impersonate}>
                <UserCheck size={14} /> Impersonate
              </button>
            )}
            {customer.status === "active" ? (
              <button className="btn-danger text-sm flex items-center gap-2" onClick={suspend} disabled={actionLoading}>
                {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <UserX size={14} />} Suspend
              </button>
            ) : (
              <button className="btn-primary text-sm flex items-center gap-2" onClick={unsuspend} disabled={actionLoading}>
                {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <UserCheck size={14} />} Unsuspend
              </button>
            )}
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Status</div>
            <div className="font-medium capitalize">{customer.status}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Plan</div>
            <div className="font-medium capitalize">{customer.plan}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Role</div>
            <div className="font-medium capitalize">{customer.role}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Domains</div>
            <div className="font-medium">{customer.domain_count}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Mailboxes</div>
            <div className="font-medium">{customer.mailbox_count}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Subscription</div>
            <div className="font-medium">{customer.subscription_status || "—"}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">2FA</div>
            <div className="font-medium">{customer.totp_enabled ? "Enabled" : "Disabled"}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Stripe Customer</div>
            <div className="font-medium truncate">{customer.stripe_customer_id || "—"}</div>
          </div>
          <div className="bg-surface-alt rounded-lg p-3">
            <div className="text-muted text-xs uppercase">Joined</div>
            <div className="font-medium">{new Date(customer.created_at).toLocaleDateString()}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
