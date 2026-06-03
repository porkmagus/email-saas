import { Link } from "react-router-dom";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-surface-alt">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
        <div className="card p-6 space-y-4 text-sm leading-relaxed text-primary">
          <p>
            Email SaaS is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your personal information.
          </p>
          <h2 className="font-semibold text-base mt-4">1. Information We Collect</h2>
          <p>
            We collect email addresses, display names, billing information via Stripe, and usage data related to your domains and mailboxes.
          </p>
          <h2 className="font-semibold text-base mt-4">2. How We Use Your Data</h2>
          <p>
            We use your data to provide email hosting services, process payments, send transactional notifications, and comply with legal obligations.
          </p>
          <h2 className="font-semibold text-base mt-4">3. Data Sharing</h2>
          <p>
            We share payment data with Stripe for billing. We do not sell your personal data to third parties.
          </p>
          <h2 className="font-semibold text-base mt-4">4. Cookies</h2>
          <p>
            We use essential cookies for authentication and session management. We may add analytics cookies with your consent.
          </p>
          <h2 className="font-semibold text-base mt-4">5. Your Rights</h2>
          <p>
            You can request deletion of your account and data. We retain audit logs for up to one year as required by law.
          </p>
          <p className="text-muted mt-4">Last updated: June 2026</p>
        </div>
        <div className="mt-6 text-center">
          <Link to="/" className="text-accent hover:underline text-sm">Back to home</Link>
        </div>
      </div>
    </div>
  );
}
