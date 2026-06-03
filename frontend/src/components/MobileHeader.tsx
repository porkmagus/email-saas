import { useAuth } from "../context/AuthContext";

export default function MobileHeader() {
  const { account } = useAuth();
  if (!account) return null;
  return (
    <div className="lg:hidden h-14 border-b border-border bg-surface flex items-center px-4 pl-14">
      <span className="font-semibold text-sm">Email SaaS</span>
    </div>
  );
}
