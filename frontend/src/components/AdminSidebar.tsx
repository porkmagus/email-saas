import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  BarChart3,
  Users,
  Wrench,
  HelpCircle,
  ClipboardList,
  ArrowLeft,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

const adminNavItems = [
  { to: "/admin", label: "Overview", icon: BarChart3 },
  { to: "/admin/customers", label: "Customers", icon: Users },
  { to: "/admin/jobs", label: "Provisioning", icon: Wrench },
  { to: "/admin/tickets", label: "Tickets", icon: HelpCircle },
  { to: "/admin/audit-log", label: "Audit Log", icon: ClipboardList },
];

export default function AdminSidebar() {
  const { logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

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
          <span className="font-semibold text-lg">Admin Panel</span>
          <button className="lg:hidden" onClick={() => setMobileOpen(false)}>
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {adminNavItems.map((item) => (
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
          <NavLink
            to="/dashboard"
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted hover:text-primary hover:bg-surface-alt"
          >
            <ArrowLeft size={18} />
            Back to Portal
          </NavLink>
        </nav>
        <div className="px-4 py-4 border-t border-border">
          <button
            onClick={logout}
            className="flex items-center gap-2 text-sm text-danger hover:opacity-80"
          >
            <LogOut size={16} />
            Log out
          </button>
        </div>
      </aside>
    </>
  );
}
