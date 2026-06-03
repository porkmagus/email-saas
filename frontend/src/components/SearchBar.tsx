import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import { Search, Loader2, Mail, BookUser, FileText, StickyNote, X } from "lucide-react";

interface SearchResultItem {
  id: string;
  type: "email" | "contact" | "file" | "note";
  title: string;
  subtitle?: string;
  meta?: string;
  url: string;
}

const tabs = [
  { key: "all", label: "All" },
  { key: "emails", label: "Emails" },
  { key: "contacts", label: "Contacts" },
  { key: "files", label: "Files" },
  { key: "notes", label: "Notes" },
] as const;

type Scope = (typeof tabs)[number]["key"];

function debounce<T extends (...args: any[]) => void>(fn: T, wait: number) {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), wait);
  };
}

export default function SearchBar() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<Scope>("all");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { addToast } = useToast();

  const performSearch = useCallback(
    async (q: string, s: Scope) => {
      if (!q.trim()) {
        setResults([]);
        setTotal(0);
        return;
      }
      setLoading(true);
      try {
        const res = await api.post<{
          emails: { id: string; subject: string; from_addr: string; snippet: string | null; received_at: string; folder: string }[];
          contacts: { id: string; name: string | null; email: string; is_vip: boolean }[];
          files: { id: string; filename: string; size: number; created_at: string }[];
          notes: { id: string; title: string; content_preview: string | null; created_at: string }[];
          total: number;
        }>("/search", { q: q.trim(), scope: s === "all" ? null : s, limit: 20 });
        const data = res.data;
        const items: SearchResultItem[] = [
          ...data.emails.map((e) => ({
            id: e.id,
            type: "email" as const,
            title: e.subject,
            subtitle: e.from_addr,
            meta: e.snippet ? e.snippet.slice(0, 80) : undefined,
            url: `/outbox`, // close enough for now
          })),
          ...data.contacts.map((c) => ({
            id: c.id,
            type: "contact" as const,
            title: c.name || c.email,
            subtitle: c.email,
            meta: c.is_vip ? "VIP" : undefined,
            url: `/contacts`,
          })),
          ...data.files.map((f) => ({
            id: f.id,
            type: "file" as const,
            title: f.filename,
            subtitle: `${f.size} bytes`,
            meta: undefined,
            url: `/files`,
          })),
          ...data.notes.map((n) => ({
            id: n.id,
            type: "note" as const,
            title: n.title,
            subtitle: n.content_preview ? n.content_preview.slice(0, 80) : undefined,
            meta: undefined,
            url: `/notes`,
          })),
        ];
        setResults(items);
        setTotal(data.total);
      } catch (err: any) {
        addToast(err?.response?.data?.detail || "Search failed", "error");
      } finally {
        setLoading(false);
      }
    },
    [addToast]
  );

  const debouncedSearch = useRef(debounce(performSearch, 300)).current;

  useEffect(() => {
    debouncedSearch(query, scope);
  }, [query, scope, debouncedSearch]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && !open && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const iconForType = (type: string) => {
    switch (type) {
      case "email":
        return <Mail size={16} className="text-accent" />;
      case "contact":
        return <BookUser size={16} className="text-success" />;
      case "file":
        return <FileText size={16} className="text-warning" />;
      case "note":
        return <StickyNote size={16} className="text-muted" />;
      default:
        return <Search size={16} />;
    }
  };

  return (
    <div ref={containerRef} className="relative flex-1 max-w-xl mx-4">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          ref={inputRef}
          className="w-full pl-9 pr-8 py-2 rounded-lg border border-border bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          placeholder="Search... (/ to open)"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
        />
        {query && (
          <button
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-primary"
            onClick={() => {
              setQuery("");
              setResults([]);
              inputRef.current?.focus();
            }}
          >
            <X size={14} />
          </button>
        )}
      </div>

      {open && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-surface border border-border rounded-lg shadow-xl z-50 overflow-hidden">
          <div className="flex items-center gap-1 border-b border-border px-2 py-2 overflow-x-auto">
            {tabs.map((t) => (
              <button
                key={t.key}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  scope === t.key
                    ? "bg-accent text-white"
                    : "bg-surface-alt text-muted hover:text-primary"
                }`}
                onClick={() => setScope(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center py-6">
                <Loader2 size={20} className="animate-spin text-accent" />
              </div>
            )}

            {!loading && results.length === 0 && query.trim() && (
              <div className="px-4 py-6 text-sm text-muted text-center">No results found.</div>
            )}

            {!loading && results.length === 0 && !query.trim() && (
              <div className="px-4 py-6 text-sm text-muted text-center">Start typing to search...</div>
            )}

            {results.map((item) => (
              <button
                key={`${item.type}-${item.id}`}
                className="w-full text-left flex items-start gap-3 px-4 py-3 hover:bg-surface-alt transition-colors border-b border-border last:border-b-0"
                onClick={() => {
                  setOpen(false);
                  navigate(item.url);
                }}
              >
                <div className="mt-0.5 shrink-0">{iconForType(item.type)}</div>
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{item.title}</div>
                  {item.subtitle && <div className="text-xs text-muted truncate">{item.subtitle}</div>}
                  {item.meta && <div className="text-xs text-muted truncate">{item.meta}</div>}
                </div>
              </button>
            ))}
          </div>

          {total > 0 && (
            <div className="px-4 py-2 border-t border-border text-xs text-muted text-center">
              {total} result{total === 1 ? "" : "s"}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
