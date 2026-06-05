import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Mail, Lock, User, ArrowRight, Loader2, CheckCircle } from "lucide-react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { addToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(email, password, displayName);
      addToast("Account created", "success");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Registration failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0f1e] px-4 relative">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <User size={24} className="text-white" />
            </div>
          </Link>
          <h1 className="text-2xl font-bold text-white">Create account</h1>
          <p className="text-sm text-slate-400 mt-1">Start your free 14-day trial. No credit card required.</p>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-2xl p-6 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Display name</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  className="w-full bg-[#0a0f1e] border border-white/10 rounded-lg px-4 py-3 pl-10 text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  placeholder="Jane Doe"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  className="w-full bg-[#0a0f1e] border border-white/10 rounded-lg px-4 py-3 pl-10 text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  className="w-full bg-[#0a0f1e] border border-white/10 rounded-lg px-4 py-3 pl-10 text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  placeholder="Min 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
            </div>
            <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25" disabled={loading}>
              {loading ? <Loader2 size={16} className="animate-spin" /> : <>
                Create account <ArrowRight size={16} />
              </>}
            </button>
          </form>
        </div>
        <div className="mt-6 text-center text-sm text-slate-500">
          Already have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300 transition-colors">Sign in</Link>
        </div>
        <div className="mt-8 flex items-center justify-center gap-6 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <CheckCircle size={12} className="text-emerald-400" />
            Free 14-day trial
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle size={12} className="text-emerald-400" />
            No credit card
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle size={12} className="text-emerald-400" />
            Cancel anytime
          </span>
        </div>
      </div>
    </div>
  );
}
