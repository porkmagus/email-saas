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
    <div className="min-h-screen flex items-center justify-center bg-surface-alt px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-accent/10 text-accent mb-4">
            <Mail size={24} />
          </div>
          <h1 className="text-2xl font-bold">Sign in</h1>
          <p className="text-sm text-muted mt-1">Enter your credentials to access your account.</p>
        </div>
        <div className="card p-6">
          {tempToken ? (
            <form onSubmit={handleTotp} className="space-y-4">
              <div>
                <label className="label">TOTP Code</label>
                <input
                  type="text"
                  inputMode="numeric"
                  className="input"
                  placeholder="123456"
                  maxLength={6}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                {loading ? <Loader2 size={16} className="animate-spin" /> : <>
                  Verify <ArrowRight size={16} />
                </>}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Email</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    type="email"
                    className="input pl-9"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    type="password"
                    className="input pl-9"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                {loading ? <Loader2 size={16} className="animate-spin" /> : <>
                  Sign in <ArrowRight size={16} />
                </>}
              </button>
            </form>
          )}
        </div>
        <div className="mt-6 text-center text-sm text-muted">
          <Link to="/reset-password" className="text-accent hover:underline">Forgot password?</Link>
          <span className="mx-2">·</span>
          <Link to="/register" className="text-accent hover:underline">Create account</Link>
        </div>
      </div>
    </div>
  );
}
