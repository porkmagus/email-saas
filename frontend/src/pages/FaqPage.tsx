import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Mail,
  Menu,
  X,
  ChevronDown,
  ArrowRight,
  HelpCircle,
} from "lucide-react";
import { useState } from "react";

const faqs = [
  {
    q: "Can I use my own domain?",
    a: "Yes. Add your domain in the dashboard, copy the DNS records we provide, and we'll verify them automatically. Email is usually flowing within minutes.",
  },
  {
    q: "How does the webmail work?",
    a: "Every domain gets a branded Roundcube webmail instance accessible via SSO from your dashboard. No separate passwords or logins needed.",
  },
  {
    q: "What email protocols are supported?",
    a: "Full SMTP, IMAP, and JMAP support. Use any desktop or mobile client (Thunderbird, Apple Mail, Outlook, etc.) or our webmail.",
  },
  {
    q: "How do I cancel or downgrade?",
    a: "Cancel, downgrade, or upgrade anytime via the Stripe Customer Portal in your billing settings. No lock-in, no questions asked.",
  },
  {
    q: "Is there an API?",
    a: "Yes. Generate scoped API keys with granular permissions for user management, domain provisioning, billing, and analytics.",
  },
  {
    q: "What about spam and viruses?",
    a: "Built-in spam filtering with SPF, DKIM, and DMARC verification. Plus Bayesian filtering and custom email rules.",
  },
  {
    q: "Do you support passkeys?",
    a: "Yes. We support FIDO2/WebAuthn passkeys for passwordless authentication. You can also use TOTP-based 2FA or app passwords.",
  },
  {
    q: "Can I import from Gmail or another provider?",
    a: "Yes. Use our import tool to migrate mailboxes, contacts, and calendars from Gmail, Outlook, or any IMAP-compatible provider.",
  },
  {
    q: "What is your uptime SLA?",
    a: "99.9% uptime SLA on all plans. Enterprise plans include a custom SLA with dedicated support and priority incident response.",
  },
  {
    q: "Is my data encrypted?",
    a: "All data is encrypted at rest and in transit using TLS 1.3. We use a zero-knowledge architecture where possible.",
  },
];

export default function FaqPage() {
  const { account } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-white">
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0f1e]/90 backdrop-blur-md border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#2563eb] rounded-lg flex items-center justify-center">
              <Mail className="text-white" size={16} />
            </div>
            <span className="font-semibold text-lg tracking-tight">NexusMail</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm">
            <Link to="/" className="text-slate-300 hover:text-white transition-colors">Features</Link>
            <Link to="/pricing" className="text-slate-300 hover:text-white transition-colors">Pricing</Link>
            <Link to="/faq" className="text-white transition-colors">FAQ</Link>
            <Link to="/status" className="text-slate-300 hover:text-white transition-colors">Status</Link>
            {account ? (
              <Link to="/dashboard" className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-5 py-2 rounded-lg font-medium transition-colors">
                Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-slate-300 hover:text-white transition-colors">Sign in</Link>
                <Link to="/register" className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-5 py-2 rounded-lg font-medium transition-colors">
                  Get started
                </Link>
              </>
            )}
          </nav>
          <button className="md:hidden text-white" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
        {mobileOpen && (
          <div className="md:hidden px-4 pb-4 space-y-3 border-t border-white/5 bg-[#0a0f1e]/95 backdrop-blur-md">
            <Link to="/" className="block text-sm text-slate-300 py-2">Features</Link>
            <Link to="/pricing" className="block text-sm text-slate-300 py-2">Pricing</Link>
            <Link to="/faq" className="block text-sm text-white py-2">FAQ</Link>
            <Link to="/status" className="block text-sm text-slate-300 py-2">Status</Link>
            {account ? (
              <Link to="/dashboard" className="block text-sm text-blue-400 py-2">Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="block text-sm text-slate-300 py-2">Sign in</Link>
                <Link to="/register" className="block text-sm text-blue-400 py-2">Get started</Link>
              </>
            )}
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="pt-32 pb-12 sm:pt-40 sm:pb-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-[#2563eb]/10 rounded-lg flex items-center justify-center">
              <HelpCircle size={20} className="text-[#3b82f6]" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold">Frequently asked questions</h1>
              <p className="text-slate-400 mt-1">Everything you need to know about NexusMail.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Content */}
      <section className="pb-20 sm:pb-28">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden">
                <button
                  className="w-full flex items-center justify-between p-5 text-left"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                >
                  <span className="font-medium pr-4">{faq.q}</span>
                  <ChevronDown
                    size={20}
                    className={`text-slate-400 shrink-0 transition-transform ${openFaq === i ? "rotate-180" : ""}`}
                  />
                </button>
                <div className={`overflow-hidden transition-all duration-300 ${openFaq === i ? "max-h-48" : "max-h-0"}`}>
                  <p className="px-5 pb-5 text-sm text-slate-400 leading-relaxed">{faq.a}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 bg-[#0d1321] border border-white/10 rounded-xl p-6 text-center">
            <p className="text-lg text-slate-300 mb-4">Still have questions?</p>
            <Link
              to="/register"
              className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2"
            >
              Start a free trial <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-[#2563eb] rounded-lg flex items-center justify-center">
                  <Mail className="text-white" size={16} />
                </div>
                <span className="font-semibold">NexusMail</span>
              </div>
              <p className="text-sm text-slate-400">
                Modern email hosting for teams who demand the best.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-sm">Product</h4>
              <div className="space-y-2 text-sm">
                <Link to="/" className="block text-slate-400 hover:text-white transition-colors">Features</Link>
                <Link to="/pricing" className="block text-slate-400 hover:text-white transition-colors">Pricing</Link>
                <Link to="/faq" className="block text-slate-400 hover:text-white transition-colors">FAQ</Link>
                <Link to="/status" className="block text-slate-400 hover:text-white transition-colors">Status</Link>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-sm">Company</h4>
              <div className="space-y-2 text-sm">
                <Link to="/tos" className="block text-slate-400 hover:text-white transition-colors">Terms</Link>
                <Link to="/privacy" className="block text-slate-400 hover:text-white transition-colors">Privacy</Link>
                <Link to="/aup" className="block text-slate-400 hover:text-white transition-colors">AUP</Link>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-sm">Contact</h4>
              <div className="space-y-2 text-sm">
                <a href="mailto:support@nexusmail.com" className="block text-slate-400 hover:text-white transition-colors">support@nexusmail.com</a>
              </div>
            </div>
          </div>
          <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
            <div> NexusMail. All rights reserved.</div>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                All systems operational
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
