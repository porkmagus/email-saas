import { useState } from "react";
import { Link } from "react-router-dom";
import { useToast } from "../context/ToastContext";
import { api } from "../api/client";
import { Mail, ArrowRight, Loader2, CheckCircle } from "lucide-react";

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { addToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/auth/reset-password/request", { email });
      setSent(true);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Request failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-alt px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">Reset password</h1>
          <p className="text-sm text-muted mt-1">We will send a reset link to your email.</p>
        </div>
        <div className="card p-6">
          {sent ? (
            <div className="text-center py-4">
              <CheckCircle className="mx-auto text-success mb-2" size={32} />
              <p className="text-sm">If that email exists, a reset link was sent.</p>
            </div>
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
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                {loading ? <Loader2 size={16} className="animate-spin" /> : <>
                  Send link <ArrowRight size={16} />
                </>}
              </button>
            </form>
          )}
        </div>
        <div className="mt-6 text-center text-sm text-muted">
          <Link to="/login" className="text-accent hover:underline">Back to sign in</Link>
        </div>
      </div>
    </div>
  );
}
