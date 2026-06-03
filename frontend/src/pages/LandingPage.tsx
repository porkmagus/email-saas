import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Mail,
  Shield,
  Globe,
  CreditCard,
  ArrowRight,
  CheckCircle,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

const features = [
  {
    icon: Mail,
    title: "Reliable Email Hosting",
    desc: "Powered by Stalwart Mail Server with SMTP, IMAP, and JMAP support.",
  },
  {
    icon: Shield,
    title: "Built-in Security",
    desc: "DKIM, SPF, DMARC, and TLS out of the box. Optional TOTP 2FA.",
  },
  {
    icon: Globe,
    title: "Custom Domains",
    desc: "Bring your own domain with automated DNS verification and onboarding.",
  },
  {
    icon: CreditCard,
    title: "Stripe Billing",
    desc: "Subscription management, usage metering, and self-serve upgrades.",
  },
];

const pricing = [
  {
    name: "Starter",
    price: "$10",
    period: "/month",
    features: ["1 Domain", "5 Mailboxes", "10GB Storage", "Basic Support"],
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    features: ["5 Domains", "25 Mailboxes", "50GB Storage", "Priority Support"],
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "/month",
    features: ["20 Domains", "100 Mailboxes", "500GB Storage", "500 emails/day (after warm-up)", "Dedicated Support"],
  },
];

const faqs = [
  {
    q: "Can I use my own domain?",
    a: "Yes. Add your domain in the portal, copy the DNS records we provide, and verify.",
  },
  {
    q: "Do you offer webmail?",
    a: "Yes. Every domain gets a branded Roundcube webmail URL with SSO.",
  },
  {
    q: "How do I cancel?",
    a: "You can cancel anytime via the Stripe Customer Portal in your billing settings.",
  },
  {
    q: "Is there an API?",
    a: "Yes. Generate scoped API keys in Settings for programmatic access.",
  },
];

export default function LandingPage() {
  const { account } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface-alt">
      <header className="bg-surface border-b border-border sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-lg">
            <Mail className="text-accent" size={22} />
            Email SaaS
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <a href="#features" className="text-muted hover:text-primary">Features</a>
            <a href="#pricing" className="text-muted hover:text-primary">Pricing</a>
            <a href="#faq" className="text-muted hover:text-primary">FAQ</a>
            <a href="/status" className="text-muted hover:text-primary">Status</a>
            {account ? (
              <Link to="/dashboard" className="btn-primary">Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="text-muted hover:text-primary">Sign in</Link>
                <Link to="/register" className="btn-primary">Get started</Link>
              </>
            )}
          </nav>
          <button className="md:hidden" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
        {mobileOpen && (
          <div className="md:hidden px-4 pb-4 space-y-2">
            <a href="#features" className="block text-sm text-muted">Features</a>
            <a href="#pricing" className="block text-sm text-muted">Pricing</a>
            <a href="#faq" className="block text-sm text-muted">FAQ</a>
            <a href="/status" className="block text-sm text-muted">Status</a>
            {account ? (
              <Link to="/dashboard" className="block text-sm text-accent">Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="block text-sm text-muted">Sign in</Link>
                <Link to="/register" className="block text-sm text-accent">Get started</Link>
              </>
            )}
          </div>
        )}
      </header>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-primary">
          Email hosting for modern teams
        </h1>
        <p className="mt-4 text-lg text-muted max-w-2xl mx-auto">
          Custom domains, mailboxes, and webmail with automated provisioning, Stripe billing, and built-in support.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          {account ? (
            <Link to="/dashboard" className="btn-primary inline-flex items-center gap-2">
              Dashboard <ArrowRight size={16} />
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn-primary inline-flex items-center gap-2">
                Get started <ArrowRight size={16} />
              </Link>
              <Link to="/login" className="btn-secondary">Sign in</Link>
            </>
          )}
        </div>
      </section>

      <section id="features" className="max-w-6xl mx-auto px-4 sm:px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-10">Features</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f) => (
            <div key={f.title} className="card p-6">
              <f.icon className="text-accent mb-3" size={24} />
              <h3 className="font-semibold text-primary">{f.title}</h3>
              <p className="text-sm text-muted mt-1">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="max-w-6xl mx-auto px-4 sm:px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-10">Pricing</h2>
        <div className="grid sm:grid-cols-3 gap-6">
          {pricing.map((p) => (
            <div key={p.name} className="card p-6 flex flex-col">
              <h3 className="font-semibold text-lg">{p.name}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-3xl font-bold">{p.price}</span>
                <span className="text-sm text-muted">{p.period}</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm flex-1">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <CheckCircle size={14} className="text-success" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="btn-primary mt-6 block text-center">
                Get started
              </Link>
            </div>
          ))}
        </div>
      </section>

      <section id="faq" className="max-w-3xl mx-auto px-4 sm:px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-10">FAQ</h2>
        <div className="space-y-4">
          {faqs.map((faq) => (
            <div key={faq.q} className="card p-4">
              <h3 className="font-semibold text-primary">{faq.q}</h3>
              <p className="text-sm text-muted mt-1">{faq.a}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-border bg-surface py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted">
          <div className="flex items-center gap-2">
            <Mail size={16} className="text-accent" />
            Email SaaS
          </div>
          <div className="flex items-center gap-4">
            <Link to="/tos" className="hover:text-primary">Terms</Link>
            <Link to="/privacy" className="hover:text-primary">Privacy</Link>
            <Link to="/aup" className="hover:text-primary">AUP</Link>
            <Link to="/status" className="hover:text-primary">Status</Link>
          </div>
          <div>Email SaaS</div>
        </div>
      </footer>
    </div>
  );
}
