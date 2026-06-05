import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { CreditCard, ArrowRight, Loader2, Shield, TrendingUp, Zap } from "lucide-react";

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
        <h1 className="text-2xl font-bold text-white">Billing</h1>
        <p className="text-sm text-slate-400">Manage your subscription and payment methods.</p>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-blue-500/10 p-3 rounded-xl text-blue-400">
            <Zap size={20} />
          </div>
          <div>
            <div className="text-sm text-slate-400">Current Plan</div>
            <div className="text-lg font-bold text-white">Starter</div>
          </div>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-emerald-500/10 p-3 rounded-xl text-emerald-400">
            <Shield size={20} />
          </div>
          <div>
            <div className="text-sm text-slate-400">Status</div>
            <div className="text-lg font-bold text-white">Active</div>
          </div>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-purple-500/10 p-3 rounded-xl text-purple-400">
            <TrendingUp size={20} />
          </div>
          <div>
            <div className="text-sm text-slate-400">Next Billing</div>
            <div className="text-lg font-bold text-white">Jul 4</div>
          </div>
        </div>
      </div>

      <div className="bg-[#0f172a] border border-white/5 rounded-xl p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="bg-blue-500/10 p-3 rounded-xl text-blue-400">
            <CreditCard size={20} />
          </div>
          <div>
            <h2 className="font-semibold text-white">Stripe Billing</h2>
            <p className="text-sm text-slate-400">Update cards, change plans, or view invoices.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 shadow-lg shadow-blue-500/25" onClick={openPortal} disabled={portalLoading}>
            {portalLoading ? <Loader2 size={16} className="animate-spin" /> : <>
              Open billing portal <ArrowRight size={16} />
            </>}
          </button>
          <button className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-4 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2" onClick={openCheckout} disabled={checkoutLoading}>
            {checkoutLoading ? <Loader2 size={16} className="animate-spin" /> : "Upgrade via checkout"}
          </button>
        </div>
      </div>

      <div className="bg-[#0f172a] border border-white/5 rounded-xl p-6">
        <h2 className="font-semibold text-white mb-2">Usage</h2>
        <p className="text-sm text-slate-400">Usage metering and overage details will appear here.</p>
      </div>
    </div>
  );
}
