import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Mail,
  Shield,
  Globe,
  Zap,
  Lock,
  Server,
  Clock,
  ArrowRight,
  CheckCircle,
  Menu,
  X,
  ChevronRight,
} from "lucide-react";
import { useState, useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

// Free stock images from Unsplash (CC0 / free to use)
const IMAGES = {
  hero: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1920&q=80&auto=format&fit=crop",
  heroRight: "https://images.unsplash.com/photo-1555421689-491a97ff2040?w=600&h=450&fit=crop&auto=format&q=80",
  features: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920&q=80&auto=format&fit=crop",
  security: "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1920&q=80&auto=format&fit=crop",
  cta: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80&auto=format&fit=crop",
};

// Section that fades in as it enters viewport and fades out as it leaves.
// This prevents background images from clashing at section boundaries.
function FadeSection({ children, className, image, imageOpacity = 0.35 }: {
  children: React.ReactNode;
  className?: string;
  image?: string;
  imageOpacity?: number;
}) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  // opacity: 0 when entering (0.0), 1 when fully in (0.15-0.85), 0 when leaving (1.0)
  const opacity = useTransform(scrollYProgress, [0, 0.15, 0.85, 1], [0, 1, 1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.15, 0.85, 1], [1.06, 1, 1, 1.06]);

  return (
    <motion.div
      ref={ref}
      style={{ opacity }}
      className={`relative overflow-hidden ${className || ""}`}
    >
      {image && (
        <motion.div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${image})`, opacity: imageOpacity, scale }}
        />
      )}
      {image && <div className="absolute inset-0 bg-[#0a0f1e]/75" />}
      <div className="relative">{children}</div>
    </motion.div>
  );
}

const features = [
  {
    icon: Shield,
    title: "Enterprise Security",
    desc: "End-to-end encryption, DKIM, SPF, DMARC, and TLS 1.3. Zero-knowledge architecture.",
  },
  {
    icon: Globe,
    title: "Custom Domains",
    desc: "Bring your own domain with automated DNS verification and MX setup in under 60 seconds.",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    desc: "Sub-100ms API responses. Built on Rust-powered Stalwart with async I/O for maximum throughput.",
  },
  {
    icon: Lock,
    title: "Zero-Trust Auth",
    desc: "FIDO2/WebAuthn passkeys, TOTP 2FA, app passwords, and scoped API keys.",
  },
  {
    icon: Server,
    title: "Built-in Webmail",
    desc: "Branded Roundcube webmail with SSO. Every domain gets its own webmail URL.",
  },
  {
    icon: Clock,
    title: "Smart Automation",
    desc: "Auto-provisioning, email rules, vacation responses, aliases, and outbox scheduling.",
  },
];

const pricing = [
  {
    name: "Basic",
    price: "$7",
    period: "/month",
    description: "For individuals and small teams",
    features: [
      "1 Custom Domain",
      "5 Mailboxes",
      "10GB Storage",
      "1,000 emails/day",
      "Basic Support",
      "Webmail Access",
      "API Access",
    ],
    popular: false,
  },
  {
    name: "Standard",
    price: "$10",
    period: "/month",
    description: "For growing teams",
    features: [
      "5 Custom Domains",
      "25 Mailboxes",
      "50GB Storage",
      "5,000 emails/day",
      "Priority Support",
      "Webmail + SSO",
      "API + Webhooks",
      "Email Rules Engine",
      "Advanced Analytics",
    ],
    popular: true,
  },
  {
    name: "Professional",
    price: "$17",
    period: "/month",
    description: "For organizations that need more",
    features: [
      "20 Custom Domains",
      "100 Mailboxes",
      "500GB Storage",
      "50,000 emails/day",
      "Dedicated Support",
      "Custom SLA",
      "White-label Options",
      "Advanced API",
      "SSO / SAML",
      "Audit Logs",
    ],
    popular: false,
  },
];

export default function LandingPage() {
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
            <Link to="/pricing" className="text-slate-300 hover:text-white transition-colors">Pricing</Link>
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
            <Link to="/pricing" className="block text-sm text-slate-300 py-2">Pricing</Link>
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

      {/* Hero Section */}
      <FadeSection className="pt-32 pb-20 sm:pt-40 sm:pb-28" image={IMAGES.hero} imageOpacity={0.25}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-tight">
                Email hosting for teams that take security seriously.
              </h1>
              <p className="mt-6 text-lg text-slate-400 leading-relaxed max-w-lg">
                Custom domains, automated provisioning, and enterprise-grade security.
                Built on open standards with straightforward billing.
              </p>
              <div className="mt-8 flex items-center gap-4 flex-wrap">
                {account ? (
                  <Link to="/dashboard" className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-7 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2">
                    Dashboard <ArrowRight size={18} />
                  </Link>
                ) : (
                  <>
                    <Link to="/register" className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-7 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2">
                      Start free trial <ArrowRight size={18} />
                    </Link>
                    <Link to="/login" className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-7 py-3 rounded-lg font-semibold transition-colors">
                      Sign in
                    </Link>
                  </>
                )}
              </div>
              <p className="mt-4 text-sm text-slate-500">
                No credit card required. 14-day free trial.
              </p>
              <div className="mt-8 flex items-center gap-6 text-sm text-slate-400">
                <span className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-emerald-400" /> TLS 1.3
                </span>
                <span className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-emerald-400" /> DKIM/SPF
                </span>
                <span className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-emerald-400" /> FIDO2
                </span>
              </div>
            </div>
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="hidden lg:block"
            >
              <img
                src={IMAGES.heroRight}
                alt="Professional workspace"
                className="rounded-xl shadow-2xl border border-white/10 w-full object-cover"
                loading="eager"
                width="600"
                height="450"
              />
            </motion.div>
          </div>
        </div>
      </FadeSection>

      {/* Trust Bar */}
      <section className="border-y border-white/5 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-slate-400">
            <span className="flex items-center gap-2">
              <Shield size={14} className="text-emerald-400" /> SOC 2 Compliant
            </span>
            <span className="flex items-center gap-2">
              <Lock size={14} className="text-emerald-400" /> Zero-knowledge
            </span>
            <span className="flex items-center gap-2">
              <Globe size={14} className="text-emerald-400" /> GDPR Ready
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle size={14} className="text-emerald-400" /> 99.9% Uptime SLA
            </span>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <FadeSection className="py-20 sm:py-28" image={IMAGES.features} imageOpacity={0.3}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold">Everything you need</h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Enterprise-grade email infrastructure without the enterprise complexity.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="bg-white/[0.02] border border-white/5 rounded-xl p-6 hover:bg-white/[0.04] hover:border-white/10 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-[#2563eb]/10 text-[#3b82f6] flex items-center justify-center mb-4">
                  <f.icon size={20} />
                </div>
                <h3 className="text-base font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </FadeSection>

      {/* Security Section */}
      <FadeSection className="border-y border-white/5 py-20 sm:py-28" image={IMAGES.security} imageOpacity={0.3}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-emerald-500/10 rounded-lg px-3 py-1.5 mb-6">
                <Shield size={14} className="text-emerald-400" />
                <span className="text-sm text-emerald-300">Security First</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">Your email is your fortress</h2>
              <p className="text-lg text-slate-400 mb-6 leading-relaxed">
                Every message is encrypted at rest and in transit. Zero-knowledge architecture means even we can't read your emails.
              </p>
              <div className="space-y-3">
                {[
                  "TLS 1.3 for all connections",
                  "DKIM, SPF, and DMARC by default",
                  "End-to-end encryption support",
                  "FIDO2/WebAuthn passkey support",
                  "Brute-force protection",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3">
                    <CheckCircle size={16} className="text-emerald-400 shrink-0" />
                    <span className="text-slate-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-[#0d1321] border border-white/10 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                  <Lock size={20} className="text-emerald-400" />
                </div>
                <div>
                  <div className="font-semibold">Security Score</div>
                  <div className="text-sm text-emerald-400">98/100 — Excellent</div>
                </div>
              </div>
              <div className="space-y-3">
                {[
                  { label: "TLS Encryption", status: "Active" },
                  { label: "DKIM Signing", status: "Verified" },
                  { label: "SPF Record", status: "Pass" },
                  { label: "DMARC Policy", status: "Enforced" },
                  { label: "2FA Protection", status: "Enabled" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-2 border-b border-white/5">
                    <span className="text-sm text-slate-400">{item.label}</span>
                    <span className="text-sm font-medium text-emerald-400">{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </FadeSection>

      {/* Pricing Teaser */}
      <FadeSection className="py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold">Simple, transparent pricing</h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Start free. Scale as you grow. No hidden fees.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {pricing.map((p) => (
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
                <ul className="space-y-3 flex-1">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-3 text-sm">
                      <CheckCircle size={16} className={p.popular ? "text-[#3b82f6]" : "text-slate-500"} />
                      <span className="text-slate-300">{f}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  to="/register"
                  className={`mt-6 block text-center py-3 rounded-lg font-semibold transition-colors ${
                    p.popular
                      ? "bg-[#2563eb] hover:bg-[#1d4ed8] text-white"
                      : "bg-white/5 hover:bg-white/10 border border-white/10 text-white"
                  }`}
                >
                  Get started
                </Link>
              </div>
            ))}
          </div>
          <div className="text-center mt-10">
            <Link to="/pricing" className="text-[#3b82f6] hover:text-[#60a5fa] text-sm font-medium inline-flex items-center gap-1 transition-colors">
              See full feature comparison <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </FadeSection>

      {/* CTA Section */}
      <FadeSection className="py-20 sm:py-28" image={IMAGES.cta} imageOpacity={0.35}>
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
              <Link to="/faq" className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-8 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2">
                Read FAQ <ChevronRight size={18} />
              </Link>
            </div>
          </div>
        </div>
      </FadeSection>

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
