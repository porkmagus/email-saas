import { Link } from "react-router-dom";

export default function AupPage() {
  return (
    <div className="min-h-screen bg-surface-alt">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-6">Acceptable Use Policy</h1>
        <div className="card p-6 space-y-4 text-sm leading-relaxed text-primary">
          <p>
            This Acceptable Use Policy (AUP) governs your use of Email SaaS services. Violation of this policy may result in immediate suspension or termination.
          </p>
          <h2 className="font-semibold text-base mt-4">1. Prohibited Content</h2>
          <p>
            You may not use our services to send spam, phishing emails, malware, or any content that is illegal, abusive, or harmful.
          </p>
          <h2 className="font-semibold text-base mt-4">2. No Bulk Unsolicited Mail</h2>
          <p>
            Sending bulk unsolicited email (spam) is strictly prohibited. All bulk email must have proper opt-in consent and unsubscribe mechanisms.
          </p>
          <h2 className="font-semibold text-base mt-4">3. Prohibited Activities</h2>
          <p>
            You may not use our services for: port scanning, hacking, distributing copyrighted material without permission, or any activity that violates applicable laws.
          </p>
          <h2 className="font-semibold text-base mt-4">4. Enforcement</h2>
          <p>
            We monitor usage and reserve the right to suspend accounts with high bounce rates, spam complaints, or blacklist listings without prior notice.
          </p>
          <h2 className="font-semibold text-base mt-4">5. Reporting Abuse</h2>
          <p>
            Report abuse to abuse@example.com. We will investigate and take appropriate action within 24 hours.
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
