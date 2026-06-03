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
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/domains", label: "Domains", icon: Globe },
  { to: "/mailboxes", label: "Mailboxes", icon: Mail },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/tickets", label: "Support", icon: HelpCircle },
  { to: "/onboarding", label: "Onboarding", icon: ListChecks },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const { account, logout, isAdmin } = useAuth();
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
          <button className="lg:hidden" onClick={() => setMobileOpen(false)}>
            <X size={20} />
          </button>
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
