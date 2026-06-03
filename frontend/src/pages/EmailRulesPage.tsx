import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  Plus,
  Trash2,
  Loader2,
  Pencil,
  Check,
  X,
  ArrowDown,
  ArrowRight,
  Shield,
  Code,
  CheckCircle,
  XCircle,
  Save,
  RotateCcw,
  AlertTriangle,
} from "lucide-react";

interface RuleCondition {
  id: string;
  field: string;
  operator: string;
  value: string;
}

interface RuleAction {
  id: string;
  action_type: string;
  target_mailbox_id: string | null;
  label: string | null;
}

interface EmailRule {
  id: string;
  name: string;
  priority: number;
  is_active: boolean;
  created_at: string;
  conditions: RuleCondition[];
  actions: RuleAction[];
}

interface SieveValidateResponse {
  valid: boolean;
  errors: string[];
}

export default function EmailRulesPage() {
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState<"rules" | "sieve">("rules");
  const [rules, setRules] = useState<EmailRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    priority: 1,
    conditions: [{ field: "from", operator: "contains", value: "" }],
    actions: [{ action_type: "move_to_mailbox", target_mailbox_id: "", label: "" }],
  });

  // Sieve editor state
  const [sieveScript, setSieveScript] = useState("");
  const [sieveLoading, setSieveLoading] = useState(false);
  const [sieveSaving, setSieveSaving] = useState(false);
  const [sieveValidating, setSieveValidating] = useState(false);
  const [sieveValidationErrors, setSieveValidationErrors] = useState<string[]>([]);
  const [sieveValidationValid, setSieveValidationValid] = useState<boolean | null>(null);

  const loadRules = async () => {
    setLoading(true);
    try {
      const res = await api.get<EmailRule[]>("/email-rules");
      setRules(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load rules", "error");
    } finally {
      setLoading(false);
    }
  };

  const loadSieveScript = async () => {
    setSieveLoading(true);
    try {
      const res = await api.get<{ script: string }>("/email-rules/sieve");
      setSieveScript(res.data.script);
      setSieveValidationErrors([]);
      setSieveValidationValid(null);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load Sieve script", "error");
    } finally {
      setSieveLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
    loadSieveScript();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/email-rules", {
        ...form,
        actions: form.actions.map((a) => ({
          ...a,
          target_mailbox_id: a.target_mailbox_id || null,
          label: a.label || null,
        })),
      });
      addToast("Rule created", "success");
      setShowForm(false);
      setForm({ name: "", priority: 1, conditions: [{ field: "from", operator: "contains", value: "" }], actions: [{ action_type: "move_to_mailbox", target_mailbox_id: "", label: "" }] });
      await loadRules();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to create rule", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this rule?")) return;
    try {
      await api.delete(`/email-rules/${id}`);
      addToast("Rule deleted", "success");
      await loadRules();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete", "error");
    }
  };

  const handleToggle = async (rule: EmailRule) => {
    try {
      await api.patch(`/email-rules/${rule.id}`, { is_active: !rule.is_active });
      addToast(`Rule ${rule.is_active ? "paused" : "activated"}`, "success");
      await loadRules();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to update", "error");
    }
  };

  const handleSieveValidate = async () => {
    setSieveValidating(true);
    setSieveValidationErrors([]);
    setSieveValidationValid(null);
    try {
      const res = await api.post<SieveValidateResponse>("/email-rules/sieve/validate", {
        script: sieveScript,
      });
      setSieveValidationValid(res.data.valid);
      setSieveValidationErrors(res.data.errors);
      if (res.data.valid) {
        addToast("Sieve script is valid", "success");
      } else {
        addToast("Sieve script has errors", "error");
      }
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to validate script", "error");
    } finally {
      setSieveValidating(false);
    }
  };

  const handleSieveSave = async () => {
    setSieveSaving(true);
    try {
      const res = await api.put<{ script: string }>("/email-rules/sieve", {
        script: sieveScript,
      });
      setSieveScript(res.data.script);
      setSieveValidationErrors([]);
      setSieveValidationValid(null);
      addToast("Sieve script saved", "success");
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Failed to save script";
      addToast(detail, "error");
    } finally {
      setSieveSaving(false);
    }
  };

  const handleSieveReset = async () => {
    await loadSieveScript();
    addToast("Sieve script reloaded", "success");
  };

  if (loading && activeTab === "rules") return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Email rules</h1>
          <p className="text-sm text-muted">Automate sorting and filtering with sieve rules.</p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 border-b border-border pb-0">
        <button
          className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors ${
            activeTab === "rules"
              ? "bg-primary text-white"
              : "text-muted hover:text-primary hover:bg-surface-alt"
          }`}
          onClick={() => setActiveTab("rules")}
        >
          <div className="flex items-center gap-2">
            <Shield size={16} />
            Rules
          </div>
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors ${
            activeTab === "sieve"
              ? "bg-primary text-white"
              : "text-muted hover:text-primary hover:bg-surface-alt"
          }`}
          onClick={() => setActiveTab("sieve")}
        >
          <div className="flex items-center gap-2">
            <Code size={16} />
            Sieve Editor
          </div>
        </button>
      </div>

      {activeTab === "rules" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div />
            <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
              <Plus size={16} />
              {showForm ? "Close" : "Add rule"}
            </button>
          </div>

          {showForm && (
            <div className="card p-4 space-y-4">
              <form onSubmit={handleCreate}>
                <div className="grid sm:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="label">Rule name</label>
                    <input className="input" required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="label">Priority</label>
                    <input className="input" type="number" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: Number(e.target.value) }))} />
                  </div>
                </div>
                <div className="mb-4">
                  <label className="label">Conditions</label>
                  {form.conditions.map((c, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <select className="input" value={c.field} onChange={(e) => {
                        const arr = [...form.conditions];
                        arr[i] = { ...c, field: e.target.value };
                        setForm((f) => ({ ...f, conditions: arr }));
                      }}>
                        <option value="from">From</option>
                        <option value="to">To</option>
                        <option value="subject">Subject</option>
                        <option value="body">Body</option>
                        <option value="has_attachment">Has attachment</option>
                      </select>
                      <select className="input" value={c.operator} onChange={(e) => {
                        const arr = [...form.conditions];
                        arr[i] = { ...c, operator: e.target.value };
                        setForm((f) => ({ ...f, conditions: arr }));
                      }}>
                        <option value="contains">Contains</option>
                        <option value="equals">Equals</option>
                        <option value="starts_with">Starts with</option>
                        <option value="ends_with">Ends with</option>
                        <option value="matches">Matches regex</option>
                      </select>
                      <input className="input" placeholder="Value" value={c.value} onChange={(e) => {
                        const arr = [...form.conditions];
                        arr[i] = { ...c, value: e.target.value };
                        setForm((f) => ({ ...f, conditions: arr }));
                      }} />
                    </div>
                  ))}
                </div>
                <div className="mb-4">
                  <label className="label">Actions</label>
                  {form.actions.map((a, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <select className="input" value={a.action_type} onChange={(e) => {
                        const arr = [...form.actions];
                        arr[i] = { ...a, action_type: e.target.value };
                        setForm((f) => ({ ...f, actions: arr }));
                      }}>
                        <option value="move_to_mailbox">Move to mailbox</option>
                        <option value="forward">Forward</option>
                        <option value="reject">Reject</option>
                        <option value="label">Add label</option>
                        <option value="flag">Flag</option>
                        <option value="vacation">Auto-reply (vacation)</option>
                        <option value="custom_sieve">Custom sieve</option>
                      </select>
                      <input className="input" placeholder="Target / Label" value={a.label || a.target_mailbox_id || ""} onChange={(e) => {
                        const arr = [...form.actions];
                        if (a.action_type === "move_to_mailbox") {
                          arr[i] = { ...a, target_mailbox_id: e.target.value };
                        } else {
                          arr[i] = { ...a, label: e.target.value };
                        }
                        setForm((f) => ({ ...f, actions: arr }));
                      }} />
                    </div>
                  ))}
                </div>
                <div className="flex justify-end">
                  <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
                    {creating ? <Loader2 size={16} className="animate-spin" /> : "Create rule"}
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="space-y-3">
            {rules.length === 0 && (
              <div className="card p-8 text-center text-muted">
                <Shield className="mx-auto mb-2" size={24} />
                No rules yet. Create your first rule above.
              </div>
            )}
            {rules.map((rule) => (
              <div key={rule.id} className="card p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-accent/10 text-accent flex items-center justify-center text-xs font-bold">{rule.priority}</div>
                    <div className="font-medium text-sm">{rule.name}</div>
                    <span className={`badge ${rule.is_active ? "badge-success" : "badge-muted"}`}>{rule.is_active ? "Active" : "Paused"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="text-muted hover:text-primary" title={rule.is_active ? "Pause" : "Activate"} onClick={() => handleToggle(rule)}>
                      {rule.is_active ? <X size={16} /> : <Check size={16} />}
                    </button>
                    <button className="text-danger hover:opacity-80" onClick={() => handleDelete(rule.id)}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <div className="text-sm space-y-1">
                  <div className="text-muted text-xs uppercase tracking-wide font-semibold">Conditions</div>
                  {rule.conditions.map((c) => (
                    <div key={c.id} className="flex items-center gap-2 text-sm">
                      <span className="font-medium">{c.field}</span>
                      <span className="text-muted">{c.operator}</span>
                      <span className="bg-surface-alt px-2 py-0.5 rounded text-xs">{c.value}</span>
                    </div>
                  ))}
                </div>
                <div className="text-sm space-y-1">
                  <div className="text-muted text-xs uppercase tracking-wide font-semibold">Actions</div>
                  {rule.actions.map((a) => (
                    <div key={a.id} className="flex items-center gap-2 text-sm">
                      <ArrowRight size={14} className="text-accent" />
                      <span className="font-medium">{a.action_type}</span>
                      {a.target_mailbox_id && <span className="text-muted text-xs">{a.target_mailbox_id}</span>}
                      {a.label && <span className="bg-surface-alt px-2 py-0.5 rounded text-xs">{a.label}</span>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "sieve" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted">
              Edit your raw Sieve script directly. For advanced users only.
            </div>
            <div className="flex items-center gap-2">
              <button
                className="btn-secondary flex items-center gap-2 text-sm"
                onClick={handleSieveValidate}
                disabled={sieveValidating}
              >
                {sieveValidating ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                Validate
              </button>
              <button
                className="btn-primary flex items-center gap-2 text-sm"
                onClick={handleSieveSave}
                disabled={sieveSaving}
              >
                {sieveSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Save
              </button>
              <button
                className="btn-secondary flex items-center gap-2 text-sm"
                onClick={handleSieveReset}
                disabled={sieveLoading}
              >
                {sieveLoading ? <Loader2 size={16} className="animate-spin" /> : <RotateCcw size={16} />}
                Reset
              </button>
            </div>
          </div>

          <div className="relative">
            <textarea
              className="w-full font-mono text-sm bg-[#1e1e2e] text-[#cdd6f4] border border-border rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-primary resize-y"
              rows={20}
              value={sieveScript}
              onChange={(e) => {
                setSieveScript(e.target.value);
                setSieveValidationValid(null);
              }}
              spellCheck={false}
              disabled={sieveLoading}
              placeholder="require [&quot;fileinto&quot;, &quot;reject&quot;];\n\n# Add your Sieve rules here..."
            />
          </div>

          {sieveValidationValid === true && sieveValidationErrors.length === 0 && (
            <div className="flex items-center gap-2 text-success text-sm">
              <CheckCircle size={16} />
              Script is valid
            </div>
          )}

          {sieveValidationErrors.length > 0 && (
            <div className="card p-4 border-danger/30 bg-danger/5">
              <div className="flex items-center gap-2 text-danger font-medium text-sm mb-2">
                <AlertTriangle size={16} />
                Validation errors
              </div>
              <ul className="space-y-1">
                {sieveValidationErrors.map((err, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-danger">
                    <XCircle size={14} />
                    {err}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
