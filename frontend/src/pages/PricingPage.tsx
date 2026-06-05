import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Mail,
  Menu,
  X,
  ArrowRight,
  Check,
  Minus,
  Shield,
  Zap,
  BarChart3,
  Headphones,
  MailOpen,
} from "lucide-react";
import { useState } from "react";

const plans = [
  {
    name: "Basic",
    price: "$7",
    period: "/month",
    description: "For individuals and small teams",
    cta: "Get started",
    popular: false,
  },
  {
    name: "Standard",
    price: "$10",
    period: "/month",
    description: "For growing teams",
    cta: "Get started",
    popular: true,
  },
  {
    name: "Professional",
    price: "$17",
    period: "/month",
    description: "For organizations that need more",
    cta: "Get started",
    popular: false,
  },
];

const features = [
  {
    category: "Core Email",
    icon: MailOpen,
    rows: [
      { label: "Custom domains", basic: "1", standard: "5", pro: "20" },
      { label: "Mailboxes", basic: "5", standard: "25", pro: "100" },
      { label: "Storage per mailbox", basic: "2 GB", standard: "10 GB", pro: "25 GB" },
      { label: "Email sending limit", basic: "1,000/day", standard: "5,000/day", pro: "50,000/day" },
      { label: "IMAP / SMTP / JMAP", basic: true, standard: true, pro: true },
      { label: "Webmail access", basic: true, standard: true, pro: true },
      { label: "Mobile & desktop apps", basic: true, standard: true, pro: true },
      { label: "Import from Gmail / Outlook", basic: true, standard: true, pro: true },
    ],
  },
  {
    category: "Security",
    icon: Shield,
    rows: [
      { label: "TLS 1.3 encryption", basic: true, standard: true, pro: true },
      { label: "DKIM / SPF / DMARC", basic: true, standard: true, pro: true },
      { label: "End-to-end encryption", basic: true, standard: true, pro: true },
      { label: "TOTP 2FA", basic: true, standard: true, pro: true },
      { label: "FIDO2 / WebAuthn passkeys", basic: false, standard: true, pro: true },
      { label: "App passwords", basic: false, standard: true, pro: true },
      { label: "Brute-force protection", basic: true, standard: true, pro: true },
      { label: "Login history & alerts", basic: true, standard: true, pro: true },
      { label: "Audit logs", basic: false, standard: false, pro: true },
    ],
  },
  {
    category: "Customization",
    icon: Zap,
    rows: [
      { label: "Email rules & filters", basic: "5", standard: "Unlimited", pro: "Unlimited" },
      { label: "Vacation auto-responder", basic: true, standard: true, pro: true },
      { label: "Email aliases", basic: "10", standard: "100", pro: "Unlimited" },
      { label: "Email signatures", basic: true, standard: true, pro: true },
      { label: "Custom branding", basic: false, standard: false, pro: true },
      { label: "White-label webmail", basic: false, standard: false, pro: true },
      { label: "Custom login page", basic: false, standard: false, pro: true },
    ],
  },
  {
    category: "Management",
    icon: BarChart3,
    rows: [
      { label: "Admin dashboard", basic: true, standard: true, pro: true },
      { label: "User management", basic: true, standard: true, pro: true },
      { label: "Domain health monitoring", basic: true, standard: true, pro: true },
      { label: "Delivery analytics", basic: false, standard: true, pro: true },
      { label: "Advanced API access", basic: false, standard: true, pro: true },
      { label: "Webhooks", basic: false, standard: true, pro: true },
      { label: "SSO / SAML integration", basic: false, standard: false, pro: true },
      { label: "Role-based access control", basic: false, standard: false, pro: true },
      { label: "Multi-tenant support", basic: false, standard: false, pro: true },
    ],
  },
  {
    category: "Support",
    icon: Headphones,
    rows: [
      { label: "Support channels", basic: "Email", standard: "Email + Chat", pro: "Email + Chat + Phone" },
      { label: "Response time", basic: "48h", standard: "24h", pro: "4h" },
      { label: "Priority queue", basic: false, standard: true, pro: true },
      { label: "Dedicated account manager", basic: false, standard: false, pro: true },
      { label: "Custom SLA", basic: false, standard: false, pro: true },
      { label: "Onboarding assistance", basic: false, standard: true, pro: true },
    ],
  },
];

function ValueCell({ value }: { value: boolean | string }) {
  if (value === true) {
    return <Check size={18} className="text-emerald-400 mx-auto" />;
  }
  if (value === false) {
    return <Minus size={18} className="text-slate-600 mx-auto" />;
  }
  return <span className="text-sm text-slate-300">{value}</span>;
}

export default function PricingPage() {
  const { account } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

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
            <Link to="/pricing" className="text-white transition-colors">Pricing</Link>
            <Link to="/faq" className="text-slate-300 hover:text-white transition-colors">FAQ</Link>
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
            <Link to="/pricing" className="block text-sm text-white py-2">Pricing</Link>
            <Link to="/faq" className="block text-sm text-slate-300 py-2">FAQ</Link>
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">Straightforward pricing.</h1>
          <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
            All plans include a 14-day free trial. No credit card required. No hidden fees.
          </p>
        </div>
      </section>

      {/* Plan Cards */}
      <section className="pb-16 sm:pb-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((p) => (
              <div key={p.name} className={`relative rounded-xl p-6 flex flex-col h-full ${
                p.popular
                  ? "bg-[#0d1321] border-2 border-[#2563eb]"
                  : "bg-white/[0.02] border border-white/5"
              }`}>
                {p.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#2563eb] text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </div>
                )}
                <div className="mb-4">
                  <h3 className="text-lg font-semibold">{p.name}</h3>
                  <p className="text-sm text-slate-400 mt-1">{p.description}</p>
                </div>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold">{p.price}</span>
                  <span className="text-slate-400">{p.period}</span>
                </div>
                <Link
                  to="/register"
                  className={`mt-auto block text-center py-3 rounded-lg font-semibold transition-colors ${
                    p.popular
                      ? "bg-[#2563eb] hover:bg-[#1d4ed8] text-white"
                      : "bg-white/5 hover:bg-white/10 border border-white/10 text-white"
                  }`}
                >
                  {p.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="border-t border-white/5 py-16 sm:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold">What's included</h2>
            <p className="mt-3 text-slate-400">Compare everything you get with each plan.</p>
          </div>

          <div className="overflow-x-auto -mx-4 px-4">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-4 px-3 text-sm font-medium text-slate-400 w-1/3">Feature</th>
                  <th className="text-center py-4 px-3 text-sm font-semibold text-slate-300 w-1/6">Basic</th>
                  <th className="text-center py-4 px-3 text-sm font-semibold text-slate-300 w-1/6">Standard</th>
                  <th className="text-center py-4 px-3 text-sm font-semibold text-slate-300 w-1/6">Professional</th>
                </tr>
              </thead>
              <tbody>
                {features.map((section, si) => (
                  <>
                    <tr key={`cat-${si}`} className="border-b border-white/5">
                      <td colSpan={4} className="py-4 px-3">
                        <div className="flex items-center gap-2 text-sm font-semibold text-[#3b82f6]">
                          <section.icon size={16} />
                          {section.category}
                        </div>
                      </td>
                    </tr>
                    {section.rows.map((row, ri) => (
                      <tr key={`row-${si}-${ri}`} className="border-b border-white/5 hover:bg-white/[0.01] transition-colors">
                        <td className="py-3 px-3 text-sm text-slate-300">{row.label}</td>
                        <td className="py-3 px-3 text-center">
                          <ValueCell value={row.basic} />
                        </td>
                        <td className="py-3 px-3 text-center">
                          <ValueCell value={row.standard} />
                        </td>
                        <td className="py-3 px-3 text-center">
                          <ValueCell value={row.pro} />
                        </td>
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Teaser */}
      <section className="border-t border-white/5 py-16 sm:py-24">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-4">Frequently asked questions</h2>
          <div className="space-y-6 text-left mt-8">
            {[
              {
                q: "Can I change plans at any time?",
                a: "Yes. Upgrade or downgrade anytime from your billing settings. Changes take effect immediately. If you downgrade, we'll prorate any difference.",
              },
              {
                q: "Is there a free trial?",
                a: "Every plan includes a 14-day free trial. No credit card required to start. You'll only be billed after the trial ends if you choose to continue.",
              },
              {
                q: "What happens when I hit my sending limit?",
                a: "We'll notify you at 80% of your limit. You can temporarily upgrade or wait for the daily reset. We never block inbound mail.",
              },
              {
                q: "Do you offer annual billing?",
                a: "Yes. Annual billing gives you 2 months free. You can switch between monthly and annual at any time.",
              },
            ].map((faq, i) => (
              <div key={i} className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                <h3 className="font-medium text-sm mb-2">{faq.q}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
          <div className="mt-8">
            <Link to="/faq" className="text-[#3b82f6] hover:text-[#60a5fa] text-sm font-medium inline-flex items-center gap-1 transition-colors">
              View all FAQ <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/5 py-16 sm:py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="bg-[#0d1321] border border-white/10 rounded-2xl p-8 sm:p-12 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Ready to get started?</h2>
            <p className="text-lg text-slate-400 mb-8 max-w-xl mx-auto">
              Start your free 14-day trial. No credit card required.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link to="/register" className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-8 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2">
                Start free trial <ArrowRight size={18} />
              </Link>
              <Link to="/faq" className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-8 py-3 rounded-lg font-semibold transition-colors">
                Read FAQ
              </Link>
            </div>
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
