import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Activity, Server, Database, HardDrive, AlertTriangle, CheckCircle } from "lucide-react";

export default function StatusPage() {
  const [health, setHealth] = useState<{ status: string; database: string; redis: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get<{
          status: string;
          database: string;
          redis: string;
        }>("/health");
        setHealth(res.data);
      } catch {
        setHealth({ status: "error", database: "error", redis: "error" });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const services = [
    { name: "API", status: health?.status === "ok" ? "ok" : "error", icon: Server },
    { name: "Database", status: health?.database === "ok" ? "ok" : "error", icon: Database },
    { name: "Redis", status: health?.redis === "ok" ? "ok" : "error", icon: HardDrive },
  ];

  return (
    <div className="min-h-screen bg-surface-alt">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="flex items-center gap-3 mb-6">
          <Activity className="text-accent" size={28} />
          <h1 className="text-3xl font-bold">System Status</h1>
        </div>
        <div className="space-y-4">
          {loading ? (
            <div className="card p-8 text-center text-muted">Checking status...</div>
          ) : (
            services.map((s) => (
              <div key={s.name} className="card p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <s.icon size={20} className={s.status === "ok" ? "text-success" : "text-danger"} />
                  <span className="font-semibold">{s.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  {s.status === "ok" ? (
                    <>
                      <CheckCircle size={16} className="text-success" />
                      <span className="text-sm text-success">Operational</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={16} className="text-danger" />
                      <span className="text-sm text-danger">Degraded</span>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
        <div className="mt-6 text-center text-sm text-muted">
          Status page updates automatically. For incidents, contact support.
        </div>
      </div>
    </div>
  );
}
