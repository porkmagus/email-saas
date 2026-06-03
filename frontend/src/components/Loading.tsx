import { Loader2 } from "lucide-react";

export default function Loading({ full = false }: { full?: boolean }) {
  if (full) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="animate-spin text-accent" size={32} />
    </div>
  );
}
