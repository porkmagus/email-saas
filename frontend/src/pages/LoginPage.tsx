import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { Mail, Lock, ArrowRight, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [tempToken, setTempToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, loginTotp } = useAuth();
  const { addToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result.totp_required && result.temp_token) {
        setTempToken(result.temp_token);
      } else {
        addToast("Logged in successfully", "success");
      }
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Login failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleTotp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tempToken) return;
    setLoading(true);
    try {
      await loginTotp(tempToken, totpCode);
      addToast("Logged in successfully", "success");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Invalid code", "error");
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
              <Mail size={24} className="text-white" />
            </div>
          </Link>
          <h1 className="text-2xl font-bold text-white">Sign in</h1>
          <p className="text-sm text-slate-400 mt-1">Enter your credentials to access your account.</p>
        </div>
        <div className="bg-[#0f172a] border border-white/5 rounded-2xl p-6 shadow-xl">
          {tempToken ? (
            <form onSubmit={handleTotp} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">TOTP Code</label>
                <input
                  type="text"
                  inputMode="numeric"
                  className="w-full bg-[#0a0f1e] border border-white/10 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  placeholder="123456"
                  maxLength={6}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2" disabled={loading}>
                {loading ? <Loader2 size={16} className="animate-spin" /> : <>
                  Verify <ArrowRight size={16} />
                </>}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
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
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
              <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25" disabled={loading}>
                {loading ? <Loader2 size={16} className="animate-spin" /> : <>
                  Sign in <ArrowRight size={16} />
                </>}
              </button>
            </form>
          )}
        </div>
        <div className="mt-6 text-center text-sm text-slate-500">
          <Link to="/reset-password" className="text-blue-400 hover:text-blue-300 transition-colors">Forgot password?</Link>
          <span className="mx-2">·</span>
          <Link to="/register" className="text-blue-400 hover:text-blue-300 transition-colors">Create account</Link>
        </div>
      </div>
    </div>
  );
}
