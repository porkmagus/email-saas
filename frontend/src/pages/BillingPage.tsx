import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { CreditCard, ArrowRight, Loader2 } from "lucide-react";

export default function BillingPage() {
  const { addToast } = useToast();
  const [portalLoading, setPortalLoading] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        // In the future, fetch subscription details here.
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const openPortal = async () => {
    setPortalLoading(true);
    try {
      const res = await api.post<{ url: string }>("/stripe/portal");
      window.location.href = res.data.url;
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to open billing portal", "error");
      setPortalLoading(false);
    }
  };

  const openCheckout = async () => {
    setCheckoutLoading(true);
    try {
      const res = await api.post<{ url: string }>("/stripe/checkout");
      window.location.href = res.data.url;
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to start checkout", "error");
      setCheckoutLoading(false);
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="text-sm text-muted">Manage your subscription and payment methods.</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="bg-accent/10 p-3 rounded-lg text-accent">
            <CreditCard size={20} />
          </div>
          <div>
            <h2 className="font-semibold">Stripe Billing</h2>
            <p className="text-sm text-muted">Update cards, change plans, or view invoices.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary flex items-center gap-2" onClick={openPortal} disabled={portalLoading}>
            {portalLoading ? <Loader2 size={16} className="animate-spin" /> : <>
              Open billing portal <ArrowRight size={16} />
            </>}
          </button>
          <button className="btn-secondary flex items-center gap-2" onClick={openCheckout} disabled={checkoutLoading}>
            {checkoutLoading ? <Loader2 size={16} className="animate-spin" /> : "Upgrade via checkout"}
          </button>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-2">Usage</h2>
        <p className="text-sm text-muted">Usage metering and overage details will appear here.</p>
      </div>
    </div>
  );
}
