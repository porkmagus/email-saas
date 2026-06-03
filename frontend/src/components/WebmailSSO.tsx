import { useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import { Globe, ExternalLink, Clock, Shield, Key } from "lucide-react";

interface WebmailTokenResponse {
  token: string;
  url: string;
}

export default function WebmailSSO() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);

  const handleOpenWebmail = async () => {
    setLoading(true);
    try {
      const res = await api.get<WebmailTokenResponse>("/auth/webmail-token");
      window.open(res.data.url, "_blank");
      addToast("Webmail opened in a new tab. Token expires in 5 minutes.", "success");
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to generate webmail token", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-4">
        <Globe size={20} className="text-accent" />
        <h2 className="font-semibold">Webmail SSO</h2>
      </div>
      <div className="flex items-start gap-4">
        <div className="flex-1 space-y-2">
          <p className="text-sm text-muted">
            Access your webmail with one-click SSO.
          </p>
          <div className="flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1">
              <Clock size={14} />
              Token expires in 5 minutes
            </span>
            <span className="flex items-center gap-1">
              <Shield size={14} />
              Single-use token
            </span>
            <span className="flex items-center gap-1">
              <Key size={14} />
              Secure redirect
            </span>
          </div>
        </div>
        <button
          onClick={handleOpenWebmail}
          disabled={loading}
          className="btn-primary text-sm flex items-center gap-2"
        >
          <ExternalLink size={14} />
          {loading ? "Generating..." : "Open Webmail"}
        </button>
      </div>
    </div>
  );
}
