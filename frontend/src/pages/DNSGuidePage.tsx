import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Globe,
  Copy,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  AlertTriangle,
  Clock,
  HelpCircle,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";

interface DNSRecord {
  name: string;
  type: string;
  value: string;
  priority: number | null;
  ttl: number;
  instructions: string;
}

interface DNSStep {
  step: number;
  title: string;
  description: string;
  records: DNSRecord[];
  tips: string[];
}

interface DNSProvider {
  name: string;
  slug: string;
  dns_url: string;
  instructions: string[];
}

interface DNSGuide {
  domain: string;
  providers: DNSProvider[];
  steps: DNSStep[];
  troubleshooting: string[];
  propagation_note: string;
  mx_server: string;
  webmail_url: string;
  dmarc_record: string;
}

export default function DNSGuidePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [guide, setGuide] = useState<DNSGuide | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string>("other");
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([1]));
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get<DNSGuide>(`/domains/${id}/dns-guide`);
        setGuide(res.data);
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Failed to load DNS guide", "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, addToast]);

  const copy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    addToast("Copied to clipboard", "success");
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleStep = (step: number) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(step)) {
        next.delete(step);
      } else {
        next.add(step);
      }
      return next;
    });
  };

  const markComplete = (step: number) => {
    setCompletedSteps((prev) => new Set([...prev, step]));
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await api.post<{ verified: boolean }>(`/domains/${id}/verify`);
      addToast(
        res.data.verified ? "Domain verified! All DNS records are correct." : "Not yet verified. Check your records and wait a few more minutes.",
        res.data.verified ? "success" : "warning"
      );
      if (res.data.verified) {
        setCompletedSteps(new Set([1, 2, 3, 4]));
      }
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Verification failed", "error");
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <Loading />;
  if (!guide) return <div className="p-6 text-muted">DNS guide not available.</div>;

  const provider = guide.providers.find((p) => p.slug === selectedProvider) || guide.providers[0];
  const progress = Math.round((completedSteps.size / guide.steps.length) * 100);

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold">DNS Setup Guide</h1>
        <p className="text-sm text-muted">
          Set up {guide.domain} to work with your email service.
        </p>
      </div>

      {/* Progress */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">{completedSteps.size} of {guide.steps.length} steps completed</span>
          <span className="text-sm font-medium">{progress}%</span>
        </div>
        <div className="w-full bg-border rounded-full h-2">
          <div className="bg-accent h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Provider Selector */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Globe size={18} className="text-accent" />
          <h2 className="font-semibold text-sm">Where is your domain registered?</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {guide.providers.map((p) => (
            <button
              key={p.slug}
              onClick={() => setSelectedProvider(p.slug)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedProvider === p.slug
                  ? "bg-accent text-white"
                  : "bg-surface-alt text-muted hover:text-primary"
              }`}
            >
              {p.name}
            </button>
          ))}
        </div>
        {provider.dns_url && (
          <a
            href={provider.dns_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-accent hover:underline flex items-center gap-1 mt-2"
          >
            Open {provider.name} DNS settings <ExternalLink size={14} />
          </a>
        )}
        <div className="mt-3 space-y-1">
          {provider.instructions.map((inst, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-muted">
              <span className="text-accent font-medium">{i + 1}.</span>
              {inst}
            </div>
          ))}
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {guide.steps.map((s) => {
          const isExpanded = expandedSteps.has(s.step);
          const isComplete = completedSteps.has(s.step);
          return (
            <div key={s.step} className={`card overflow-hidden ${isComplete ? "border-success/50" : ""}`}>
              <button
                onClick={() => toggleStep(s.step)}
                className="w-full flex items-center gap-3 p-4 text-left"
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  isComplete ? "bg-success text-white" : "bg-accent/10 text-accent"
                }`}>
                  {isComplete ? <CheckCircle size={16} /> : s.step}
                </div>
                <div className="flex-1">
                  <div className={`font-semibold text-sm ${isComplete ? "text-success" : ""}`}>{s.title}</div>
                  <div className="text-xs text-muted">{s.description}</div>
                </div>
                {isExpanded ? <ChevronUp size={18} className="text-muted" /> : <ChevronDown size={18} className="text-muted" />}
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 space-y-4">
                  {/* Records */}
                  <div className="space-y-2">
                    {s.records.map((rec, idx) => (
                      <div key={idx} className="bg-surface-alt rounded-lg p-3 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="badge bg-accent/10 text-accent text-xs">{rec.type}</span>
                          <span className="text-xs text-muted">Host: <code className="font-mono">{rec.name}</code></span>
                          {rec.priority !== null && (
                            <span className="text-xs text-muted">Priority: <code className="font-mono">{rec.priority}</code></span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <code className="flex-1 font-mono text-xs bg-surface rounded px-2 py-1 break-all">
                            {rec.value}
                          </code>
                          <button
                            onClick={() => copy(rec.value, `${s.step}-${idx}`)}
                            className="text-muted hover:text-primary flex-shrink-0"
                            title="Copy value"
                          >
                            {copiedField === `${s.step}-${idx}` ? <CheckCircle size={16} className="text-success" /> : <Copy size={16} />}
                          </button>
                        </div>
                        <p className="text-xs text-muted">{rec.instructions}</p>
                      </div>
                    ))}
                  </div>

                  {/* Tips */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-muted uppercase">Tips</div>
                    {s.tips.map((tip, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-muted">
                        <HelpCircle size={14} className="text-accent mt-0.5 flex-shrink-0" />
                        {tip}
                      </div>
                    ))}
                  </div>

                  {/* Mark complete */}
                  <button
                    onClick={() => markComplete(s.step)}
                    className={`btn-secondary text-sm w-full flex items-center justify-center gap-2 ${
                      isComplete ? "opacity-50 cursor-default" : ""
                    }`}
                    disabled={isComplete}
                  >
                    {isComplete ? (
                      <>
                        <CheckCircle size={16} /> Step completed
                      </>
                    ) : (
                      <>
                        <CheckCircle size={16} /> I added this record
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Verify & Troubleshooting */}
      <div className="card p-4 space-y-4">
        <div className="flex items-center gap-2 text-sm text-warning">
          <Clock size={16} />
          {guide.propagation_note}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="btn-primary flex items-center justify-center gap-2"
          >
            {verifying ? <RefreshCw size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            Check Verification Status
          </button>
          <button
            onClick={() => setShowTroubleshooting(!showTroubleshooting)}
            className="btn-secondary flex items-center justify-center gap-2"
          >
            <AlertTriangle size={16} />
            {showTroubleshooting ? "Hide" : "Show"} Troubleshooting
          </button>
        </div>

        {showTroubleshooting && (
          <div className="space-y-2 border-t border-border pt-3">
            <div className="text-sm font-medium">Troubleshooting</div>
            {guide.troubleshooting.map((tip, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-muted">
                <AlertTriangle size={14} className="text-warning mt-0.5 flex-shrink-0" />
                {tip}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/domains")} className="btn-secondary text-sm flex items-center gap-2">
          <ArrowRight size={16} className="rotate-180" /> Back to Domains
        </button>
        <button onClick={() => navigate(`/mail-setup`)} className="btn-primary text-sm flex items-center gap-2">
          Continue to Email Setup <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
