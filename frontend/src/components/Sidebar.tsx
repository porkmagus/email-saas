import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  Globe,
  Mail,
  CreditCard,
  Settings,
  HelpCircle,
  ListChecks,
  LogOut,
  Shield,
  Menu,
  X,
  Plug,
  AtSign,
  BookUser,
  Calendar,
  Ban,
  ShieldCheck,
  Umbrella,
  KeyRound,
  FileText,
  StickyNote,
  Fingerprint,
  LogIn,
  ShieldAlert,
  Send,
  Database,
  Download,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/domains", label: "Domains", icon: Globe },
  { to: "/mailboxes", label: "Mailboxes", icon: Mail },
  { to: "/aliases", label: "Aliases", icon: AtSign },
  { to: "/contacts", label: "Contacts", icon: BookUser },
  { to: "/calendar", label: "Calendar", icon: Calendar },
  { to: "/blocked-senders", label: "Blocked senders", icon: Ban },
  { to: "/email-rules", label: "Email rules", icon: ShieldCheck },
  { to: "/vacation-response", label: "Vacation", icon: Umbrella },
  { to: "/outbox", label: "Outbox", icon: Send },
  { to: "/app-passwords", label: "App passwords", icon: KeyRound },
  { to: "/passkeys", label: "Passkeys", icon: Fingerprint },
  { to: "/files", label: "Files", icon: FileText },
  { to: "/notes", label: "Notes", icon: StickyNote },
  { to: "/login-logs", label: "Login history", icon: LogIn },
  { to: "/sessions", label: "Sessions", icon: ShieldAlert },
  { to: "/mail-setup", label: "Connect", icon: Plug },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/tickets", label: "Support", icon: HelpCircle },
  { to: "/onboarding", label: "Onboarding", icon: ListChecks },
  { to: "/import", label: "Import", icon: Database },
  { to: "/export", label: "Export", icon: Download },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const { account, logout, isAdmin } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!account) return null;

  return (
    <>
      <button
        className="lg:hidden fixed top-3 left-3 z-40 p-2 rounded-lg bg-[#0f172a] border border-white/10 shadow-lg"
        onClick={() => setMobileOpen(true)}
      >
        <Menu size={20} className="text-white" />
      </button>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        className={`fixed lg:static top-0 left-0 z-50 h-full w-60 bg-[#0f172a] border-r border-white/5 flex flex-col transition-transform ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">N</span>
            </div>
            <span className="font-semibold text-lg text-white">NexusMail</span>
          </div>
          <button className="lg:hidden text-white" onClick={() => setMobileOpen(false)}>
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
          {isAdmin && (
            <NavLink
              to="/admin"
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`
              }
            >
              <Shield size={18} />
              Admin
            </NavLink>
          )}
        </nav>
        <div className="px-4 py-4 border-t border-white/5">
          <div className="text-sm font-medium text-white truncate">{account.email}</div>
          <div className="text-xs text-slate-500 capitalize">{account.plan} plan</div>
          <button
            onClick={logout}
            className="mt-3 flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors"
          >
            <LogOut size={16} />
            Log out
          </button>
        </div>
      </aside>
    </>
  );
}
