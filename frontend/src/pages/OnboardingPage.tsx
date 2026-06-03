import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import { CheckCircle, Circle, Globe, Mail, ArrowRight, Plug } from "lucide-react";
import { Link } from "react-router-dom";

export default function OnboardingPage() {
  const { addToast } = useToast();
  const [steps, setSteps] = useState({
    domain_added: false,
    domain_verified: false,
    mailbox_created: false,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [domainsRes, mailboxesRes] = await Promise.all([
          api.get<{ id: string; verified: boolean }[]>("/domains"),
          api.get<{ id: string }[]>("/mailboxes"),
        ]);
        const domains = domainsRes.data;
        const mailboxes = mailboxesRes.data;
        setSteps({
          domain_added: domains.length > 0,
          domain_verified: domains.some((d) => d.verified),
          mailbox_created: mailboxes.length > 0,
        });
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Failed to load onboarding", "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [addToast]);

  if (loading) return <Loading />;

  const items = [
    {
      key: "domain_added",
      label: "Add a domain",
      desc: "Add your custom domain to the account.",
      icon: Globe,
      link: "/domains",
      done: steps.domain_added,
    },
    {
      key: "domain_verified",
      label: "Verify domain DNS",
      desc: "Follow the step-by-step DNS setup guide.",
      icon: Globe,
      link: "/domains",
      done: steps.domain_verified,
    },
    {
      key: "mailbox_created",
      label: "Create a mailbox",
      desc: "Create your first email address.",
      icon: Mail,
      link: "/mailboxes",
      done: steps.mailbox_created,
    },
    {
      key: "email_setup",
      label: "Connect your email",
      desc: "Get webmail and email client settings.",
      icon: Plug,
      link: "/mail-setup",
      done: steps.mailbox_created && steps.domain_verified,
    },
  ];

  const completed = items.filter((i) => i.done).length;
  const progress = Math.round((completed / items.length) * 100);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Onboarding</h1>
        <p className="text-sm text-muted">Complete these steps to get your email service running.</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">{completed} of {items.length} completed</span>
          <span className="text-sm font-medium">{progress}%</span>
        </div>
        <div className="w-full bg-border rounded-full h-2">
          <div className="bg-accent h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.key} className={`card p-4 flex items-start gap-4 ${item.done ? "opacity-70" : ""}`}>
            <div className={`mt-0.5 ${item.done ? "text-success" : "text-muted"}`}>
              {item.done ? <CheckCircle size={22} /> : <Circle size={22} />}
            </div>
            <div className="flex-1">
              <div className="font-semibold text-sm">{item.label}</div>
              <div className="text-sm text-muted">{item.desc}</div>
            </div>
            <Link to={item.link} className="btn-secondary text-xs flex items-center gap-1">
              {item.done ? "Review" : "Go"} <ArrowRight size={14} />
            </Link>
          </div>
        ))}
      </div>

      {progress === 100 && (
        <div className="card p-6 text-center">
          <CheckCircle className="mx-auto text-success mb-2" size={32} />
          <h2 className="font-semibold">All set!</h2>
          <p className="text-sm text-muted mt-1">You are ready to send and receive email.</p>
        </div>
      )}
    </div>
  );
}
