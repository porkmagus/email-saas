import { Link } from "react-router-dom";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-surface-alt">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>
        <div className="card p-6 space-y-4 text-sm leading-relaxed text-primary">
          <p>
            Welcome to Email SaaS. By using our services, you agree to these Terms of Service.
          </p>
          <h2 className="font-semibold text-base mt-4">1. Acceptance of Terms</h2>
          <p>
            By signing up or using our email hosting services, you agree to be bound by these terms and our Acceptable Use Policy.
          </p>
          <h2 className="font-semibold text-base mt-4">2. Service Description</h2>
          <p>
            We provide email hosting, domain management, and related services. We do not guarantee uninterrupted service and reserve the right to suspend accounts for violations.
          </p>
          <h2 className="font-semibold text-base mt-4">3. Payments and Billing</h2>
          <p>
            Subscriptions are billed via Stripe. You agree to pay all fees associated with your selected plan. Refunds are handled at our discretion.
          </p>
          <h2 className="font-semibold text-base mt-4">4. Account Termination</h2>
          <p>
            We reserve the right to suspend or terminate accounts for violations of our Acceptable Use Policy, non-payment, or fraudulent activity.
          </p>
          <h2 className="font-semibold text-base mt-4">5. Limitation of Liability</h2>
          <p>
            Email SaaS is not liable for any indirect, incidental, or consequential damages arising from the use of our services.
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
