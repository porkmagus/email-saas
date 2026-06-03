import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
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
  Moon,
  Sun,
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
  { to: "/snooze", label: "Snooze", icon: Moon },
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
  const { theme, toggleTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!account) return null;

  return (
    <>
      <button
        className="lg:hidden fixed top-3 left-3 z-40 p-2 rounded-lg bg-surface border border-border shadow-sm"
        onClick={() => setMobileOpen(true)}
      >
        <Menu size={20} />
      </button>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        className={`fixed lg:static top-0 left-0 z-50 h-full w-60 bg-surface border-r border-border flex flex-col transition-transform ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-border">
          <span className="font-semibold text-lg">Email SaaS</span>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-md hover:bg-surface-alt transition-colors"
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="lg:hidden" onClick={() => setMobileOpen(false)}>
              <X size={20} />
            </button>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent/10 text-accent"
                    : "text-muted hover:text-primary hover:bg-surface-alt"
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
                    ? "bg-accent/10 text-accent"
                    : "text-muted hover:text-primary hover:bg-surface-alt"
                }`
              }
            >
              <Shield size={18} />
              Admin
            </NavLink>
          )}
        </nav>
        <div className="px-4 py-4 border-t border-border">
          <div className="text-sm font-medium truncate">{account.email}</div>
          <div className="text-xs text-muted capitalize">{account.plan} plan</div>
          <button
            onClick={logout}
            className="mt-3 flex items-center gap-2 text-sm text-danger hover:opacity-80"
          >
            <LogOut size={16} />
            Log out
          </button>
        </div>
      </aside>
    </>
  );
}
