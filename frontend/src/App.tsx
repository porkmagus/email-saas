import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import DomainsPage from "./pages/DomainsPage";
import MailboxesPage from "./pages/MailboxesPage";
import BillingPage from "./pages/BillingPage";
import SettingsPage from "./pages/SettingsPage";
import OnboardingPage from "./pages/OnboardingPage";
import TicketsPage from "./pages/TicketsPage";
import TicketDetailPage from "./pages/TicketDetailPage";
import AdminOverviewPage from "./pages/admin/AdminOverviewPage";
import AdminCustomersPage from "./pages/admin/AdminCustomersPage";
import AdminCustomerDetailPage from "./pages/admin/AdminCustomerDetailPage";
import AdminJobsPage from "./pages/admin/AdminJobsPage";
import AdminTicketsPage from "./pages/admin/AdminTicketsPage";
import AdminTicketDetailPage from "./pages/admin/AdminTicketDetailPage";
import AdminAuditLogPage from "./pages/admin/AdminAuditLogPage";
import MailSetupPage from "./pages/MailSetupPage";
import AliasesPage from "./pages/AliasesPage";
import ContactsPage from "./pages/ContactsPage";
import CalendarPage from "./pages/CalendarPage";
import BlockedSendersPage from "./pages/BlockedSendersPage";
import EmailRulesPage from "./pages/EmailRulesPage";
import VacationResponsePage from "./pages/VacationResponsePage";
import AppPasswordsPage from "./pages/AppPasswordsPage";
import FilesPage from "./pages/FilesPage";
import NotesPage from "./pages/NotesPage";
import PasskeysPage from "./pages/PasskeysPage";
import LoginLogsPage from "./pages/LoginLogsPage";
import OutboxPage from "./pages/OutboxPage";
import SnoozePage from "./pages/SnoozePage";
import SessionsPage from "./pages/SessionsPage";
import TermsPage from "./pages/TermsPage";
import PrivacyPage from "./pages/PrivacyPage";
import AupPage from "./pages/AupPage";
import StatusPage from "./pages/StatusPage";
import DNSGuidePage from "./pages/DNSGuidePage";
import ImportPage from "./pages/ImportPage";
import ExportPage from "./pages/ExportPage";
import FaqPage from "./pages/FaqPage";
import PricingPage from "./pages/PricingPage";
import Layout from "./components/Layout";
import AdminLayout from "./components/AdminLayout";
import Loading from "./components/Loading";

function RequireAuth({ children, adminOnly, superadminOnly }: { children: React.ReactNode; adminOnly?: boolean; superadminOnly?: boolean }) {
  const { account, isLoading, isAdmin, isSuperadmin } = useAuth();
  if (isLoading) return <Loading full />;
  if (!account) return <Navigate to="/login" replace />;
  if (superadminOnly && !isSuperadmin) return <Navigate to="/dashboard" replace />;
  if (adminOnly && !isAdmin) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const { account, isLoading } = useAuth();
  if (isLoading) return <Loading full />;
  if (account) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />
      <Route path="/reset-password" element={<GuestRoute><ResetPasswordPage /></GuestRoute>} />
      <Route path="/tos" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/aup" element={<AupPage />} />
      <Route path="/faq" element={<FaqPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/status" element={<StatusPage />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
        <Route path="/domains" element={<RequireAuth><DomainsPage /></RequireAuth>} />
        <Route path="/domains/:id/dns-guide" element={<RequireAuth><DNSGuidePage /></RequireAuth>} />
        <Route path="/mailboxes" element={<RequireAuth><MailboxesPage /></RequireAuth>} />
        <Route path="/mail-setup" element={<RequireAuth><MailSetupPage /></RequireAuth>} />
        <Route path="/aliases" element={<RequireAuth><AliasesPage /></RequireAuth>} />
        <Route path="/contacts" element={<RequireAuth><ContactsPage /></RequireAuth>} />
        <Route path="/calendar" element={<RequireAuth><CalendarPage /></RequireAuth>} />
        <Route path="/blocked-senders" element={<RequireAuth><BlockedSendersPage /></RequireAuth>} />
        <Route path="/email-rules" element={<RequireAuth><EmailRulesPage /></RequireAuth>} />
        <Route path="/vacation-response" element={<RequireAuth><VacationResponsePage /></RequireAuth>} />
        <Route path="/outbox" element={<RequireAuth><OutboxPage /></RequireAuth>} />
        <Route path="/snooze" element={<RequireAuth><SnoozePage /></RequireAuth>} />
        <Route path="/app-passwords" element={<RequireAuth><AppPasswordsPage /></RequireAuth>} />
        <Route path="/files" element={<RequireAuth><FilesPage /></RequireAuth>} />
        <Route path="/notes" element={<RequireAuth><NotesPage /></RequireAuth>} />
        <Route path="/passkeys" element={<RequireAuth><PasskeysPage /></RequireAuth>} />
        <Route path="/login-logs" element={<RequireAuth><LoginLogsPage /></RequireAuth>} />
        <Route path="/sessions" element={<RequireAuth><SessionsPage /></RequireAuth>} />
        <Route path="/import" element={<RequireAuth><ImportPage /></RequireAuth>} />
        <Route path="/export" element={<RequireAuth><ExportPage /></RequireAuth>} />
        <Route path="/billing" element={<RequireAuth><BillingPage /></RequireAuth>} />
        <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
        <Route path="/onboarding" element={<RequireAuth><OnboardingPage /></RequireAuth>} />
        <Route path="/tickets" element={<RequireAuth><TicketsPage /></RequireAuth>} />
        <Route path="/tickets/:id" element={<RequireAuth><TicketDetailPage /></RequireAuth>} />
      </Route>
      <Route element={<AdminLayout />}>
        <Route path="/admin" element={<RequireAuth adminOnly><AdminOverviewPage /></RequireAuth>} />
        <Route path="/admin/customers" element={<RequireAuth adminOnly><AdminCustomersPage /></RequireAuth>} />
        <Route path="/admin/customers/:id" element={<RequireAuth adminOnly><AdminCustomerDetailPage /></RequireAuth>} />
        <Route path="/admin/jobs" element={<RequireAuth adminOnly><AdminJobsPage /></RequireAuth>} />
        <Route path="/admin/tickets" element={<RequireAuth adminOnly><AdminTicketsPage /></RequireAuth>} />
        <Route path="/admin/tickets/:id" element={<RequireAuth adminOnly><AdminTicketDetailPage /></RequireAuth>} />
        <Route path="/admin/audit-log" element={<RequireAuth adminOnly><AdminAuditLogPage /></RequireAuth>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
