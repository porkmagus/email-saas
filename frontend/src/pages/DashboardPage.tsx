import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Mail,
  Globe,
  Activity,
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  ListChecks,
  Plug,
  TrendingUp,
  Shield,
  Zap,
  X,
  Sparkles,
  ChevronRight,
  Check,
  Circle,
} from "lucide-react";
import { Link } from "react-router-dom";

interface Stats {
  domain_count: number;
  mailbox_count: number;
  verified_domains: number;
  usage: {
    emails_sent: number;
    storage_bytes: number;
  };
  plan: string;
  status: string;
}

interface OnboardingStep {
  label: string;
  done: boolean;
  link: string;
}

export default function DashboardPage() {
  const { account } = useAuth();
  const { addToast } = useToast();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [onboardingDismissed, setOnboardingDismissed] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [domainsRes, mailboxesRes] = await Promise.all([
          api.get<{ id: string; verified: boolean }[]>("/domains"),
          api.get<{ id: string }[]>("/mailboxes"),
        ]);
        const domains = domainsRes.data;
        const mailboxes = mailboxesRes.data;
        const verified = domains.filter((d) => d.verified).length;
        setStats({
          domain_count: domains.length,
          mailbox_count: mailboxes.length,
          verified_domains: verified,
          usage: { emails_sent: 0, storage_bytes: 0 },
          plan: account?.plan || "starter",
          status: account?.status || "active",
        });
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Failed to load dashboard", "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [account, addToast]);

  if (loading) return <Loading />;

  const isSuspended = account?.status === "suspended";

  const onboardingSteps: OnboardingStep[] = [
    { label: "Add your domain", done: (stats?.domain_count || 0) > 0, link: "/domains" },
    { label: "Create a mailbox", done: (stats?.mailbox_count || 0) > 0, link: "/mailboxes" },
    { label: "Verify domain DNS", done: (stats?.verified_domains || 0) > 0, link: "/domains" },
  ];
  const completedSteps = onboardingSteps.filter((s) => s.done).length;
  const onboardingComplete = completedSteps === onboardingSteps.length;
  const showOnboarding = !onboardingComplete && !onboardingDismissed;

  return (
    <div className="space-y-6">
      {/* Onboarding Banner — Top, Glowing, First Thing */}
      {showOnboarding && (
        <div className="relative overflow-hidden rounded-2xl border border-blue-500/30 bg-gradient-to-r from-blue-600/20 to-purple-600/20 p-6 shadow-lg shadow-blue-500/10">
          {/* Animated glow effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-blue-500/10 animate-pulse" />
          <div className="relative flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={18} className="text-blue-400" />
                <h2 className="text-lg font-bold text-white">Welcome to NexusMail</h2>
              </div>
              <p className="text-sm text-slate-400 mb-4">
                Complete these steps to get your email up and running.
              </p>
              <div className="flex flex-wrap gap-3">
                {onboardingSteps.map((step, i) => (
                  <Link
                    key={i}
                    to={step.link}
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      step.done
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-white/5 text-slate-300 border border-white/10 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {step.done ? (
                      <Check size={16} className="text-emerald-400" />
                    ) : (
                      <Circle size={16} className="text-slate-500" />
                    )}
                    {step.label}
                    {!step.done && <ChevronRight size={14} />}
                  </Link>
                ))}
              </div>
              <div className="mt-4 w-full max-w-md bg-white/10 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(completedSteps / onboardingSteps.length) * 100}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {completedSteps} of {onboardingSteps.length} completed
              </p>
            </div>
            <button
              onClick={() => setOnboardingDismissed(true)}
              className="text-slate-500 hover:text-white transition-colors p-1"
              title="Dismiss"
            >
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      {isSuspended && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-4 py-3 flex items-center gap-3 text-sm">
          <AlertTriangle size={18} />
          Your account is suspended. Please check your billing or contact support.
        </div>
      )}

      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-sm text-slate-400">Welcome back, {account?.display_name || account?.email}.</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-blue-500/10 p-3 rounded-xl text-blue-400">
            <Globe size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.domain_count || 0}</div>
            <div className="text-xs text-slate-500">Domains</div>
          </div>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-purple-500/10 p-3 rounded-xl text-purple-400">
            <Mail size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.mailbox_count || 0}</div>
            <div className="text-xs text-slate-500">Mailboxes</div>
          </div>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-emerald-500/10 p-3 rounded-xl text-emerald-400">
            <CheckCircle size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.verified_domains || 0}</div>
            <div className="text-xs text-slate-500">Verified domains</div>
          </div>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="bg-amber-500/10 p-3 rounded-xl text-amber-400">
            <Activity size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold capitalize text-white">{stats?.plan}</div>
            <div className="text-xs text-slate-500">Plan</div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white">Quick Actions</h2>
          </div>
          <div className="space-y-2">
            <Link to="/domains" className="flex items-center justify-between p-3 rounded-lg border border-white/5 hover:bg-white/5 transition-colors group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
                  <Globe size={14} className="text-blue-400" />
                </div>
                <span className="text-sm font-medium text-slate-300 group-hover:text-white">Add a domain</span>
              </div>
              <ArrowRight size={16} className="text-slate-500" />
            </Link>
            <Link to="/mailboxes" className="flex items-center justify-between p-3 rounded-lg border border-white/5 hover:bg-white/5 transition-colors group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-purple-500/10 rounded-lg flex items-center justify-center">
                  <Mail size={14} className="text-purple-400" />
                </div>
                <span className="text-sm font-medium text-slate-300 group-hover:text-white">Create a mailbox</span>
              </div>
              <ArrowRight size={16} className="text-slate-500" />
            </Link>
            <Link to="/mail-setup" className="flex items-center justify-between p-3 rounded-lg border border-white/5 hover:bg-white/5 transition-colors group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                  <Plug size={14} className="text-emerald-400" />
                </div>
                <span className="text-sm font-medium text-slate-300 group-hover:text-white">Email client setup</span>
              </div>
              <ArrowRight size={16} className="text-slate-500" />
            </Link>
            <Link to="/tickets" className="flex items-center justify-between p-3 rounded-lg border border-white/5 hover:bg-white/5 transition-colors group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-amber-500/10 rounded-lg flex items-center justify-center">
                  <Shield size={14} className="text-amber-400" />
                </div>
                <span className="text-sm font-medium text-slate-300 group-hover:text-white">Open a support ticket</span>
              </div>
              <ArrowRight size={16} className="text-slate-500" />
            </Link>
          </div>
        </div>

        <div className="bg-[#0f172a] border border-white/5 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white">Onboarding</h2>
            <Link to="/onboarding" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
              View checklist <ListChecks size={14} />
            </Link>
          </div>
          <div className="w-full bg-white/5 rounded-full h-2 mb-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
              style={{ width: `${Math.min(100, (stats?.verified_domains || 0) * 33 + (stats?.mailbox_count || 0) * 33)}%` }}
            />
          </div>
          <p className="text-xs text-slate-500">Complete your setup to get the most out of your account.</p>
        </div>
      </div>

      <div className="bg-[#0f172a] border border-white/5 rounded-xl p-6">
        <h2 className="font-semibold text-white mb-4">Recent Activity</h2>
        <div className="flex items-center gap-3 py-3 border-b border-white/5">
          <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
            <Zap size={14} className="text-blue-400" />
          </div>
          <div className="flex-1">
            <div className="text-sm text-slate-300">Account created</div>
            <div className="text-xs text-slate-500">Welcome to NexusMail</div>
          </div>
          <div className="text-xs text-slate-500">Just now</div>
        </div>
        <div className="flex items-center gap-3 py-3">
          <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center">
            <TrendingUp size={14} className="text-emerald-400" />
          </div>
          <div className="flex-1">
            <div className="text-sm text-slate-300">Onboarding started</div>
            <div className="text-xs text-slate-500">Complete your setup checklist</div>
          </div>
          <div className="text-xs text-slate-500">Just now</div>
        </div>
      </div>
    </div>
  );
}
