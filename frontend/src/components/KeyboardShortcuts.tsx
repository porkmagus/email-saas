import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../context/ToastContext";
import { useTheme } from "../context/ThemeContext";
import {
  Globe,
  Mail,
  Calendar,
  AtSign,
  CreditCard,
  Settings,
  HelpCircle,
  Send,
  Plus,
  Search,
  Moon,
  Keyboard,
  X,
  ChevronRight,
} from "lucide-react";

interface ShortcutDef {
  keys: string;
  label: string;
  icon: React.ReactNode;
}

const shortcuts: ShortcutDef[] = [
  { keys: "?", label: "Show/hide this help", icon: <Keyboard size={16} /> },
  { keys: "Esc", label: "Close overlay / modal", icon: <X size={16} /> },
  { keys: "g d", label: "Go to Domains", icon: <Globe size={16} /> },
  { keys: "g m", label: "Go to Mailboxes", icon: <Mail size={16} /> },
  { keys: "g c", label: "Go to Calendar", icon: <Calendar size={16} /> },
  { keys: "g a", label: "Go to Aliases", icon: <AtSign size={16} /> },
  { keys: "g b", label: "Go to Billing", icon: <CreditCard size={16} /> },
  { keys: "g s", label: "Go to Settings", icon: <Settings size={16} /> },
  { keys: "g t", label: "Go to Tickets", icon: <HelpCircle size={16} /> },
  { keys: "g o", label: "Go to Outbox", icon: <Send size={16} /> },
  { keys: "n n", label: "New item", icon: <Plus size={16} /> },
  { keys: "/", label: "Focus search", icon: <Search size={16} /> },
  { keys: "t", label: "Toggle theme", icon: <Moon size={16} /> },
];

const gShortcuts: Record<string, string> = {
  d: "/domains",
  m: "/mailboxes",
  c: "/calendar",
  a: "/aliases",
  b: "/billing",
  s: "/settings",
  t: "/tickets",
  o: "/outbox",
};

type Sequence = null | "g" | "n";

export default function KeyboardShortcuts() {
  const [open, setOpen] = useState(false);
  const [sequence, setSequence] = useState<Sequence>(null);
  const seqTimeoutRef = useRef<number | null>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { theme, toggleTheme } = useTheme();

  const clearSeqTimeout = useCallback(() => {
    if (seqTimeoutRef.current !== null) {
      window.clearTimeout(seqTimeoutRef.current);
      seqTimeoutRef.current = null;
    }
  }, []);

  const resetSequence = useCallback(() => {
    setSequence(null);
    clearSeqTimeout();
  }, [clearSeqTimeout]);

  const startSequence = useCallback(
    (prefix: Sequence) => {
      setSequence(prefix);
      clearSeqTimeout();
      seqTimeoutRef.current = window.setTimeout(() => {
        setSequence(null);
        seqTimeoutRef.current = null;
      }, 1000);
    },
    [clearSeqTimeout]
  );

  useEffect(() => {
    if (open && closeBtnRef.current) {
      closeBtnRef.current.focus();
    }
  }, [open]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      const isInput =
        tag === "input" || tag === "textarea" || tag === "select" || (e.target as HTMLElement)?.isContentEditable;

      if (e.key === "Escape") {
        if (open) {
          e.preventDefault();
          setOpen(false);
          return;
        }
        return;
      }

      if (isInput) {
        return;
      }

      // Handle active sequences
      if (sequence === "g") {
        const path = gShortcuts[e.key.toLowerCase()];
        if (path) {
          e.preventDefault();
          resetSequence();
          navigate(path);
          return;
        }
        // Unknown key after g: cancel sequence
        resetSequence();
        return;
      }

      if (sequence === "n") {
        if (e.key === "n") {
          e.preventDefault();
          resetSequence();
          addToast("Create new item — not yet implemented", "info");
          return;
        }
        // Unknown key after n: cancel sequence
        resetSequence();
        return;
      }

      if (e.key === "g") {
        e.preventDefault();
        startSequence("g");
        return;
      }

      if (e.key === "n") {
        e.preventDefault();
        startSequence("n");
        return;
      }

      if (e.key === "?") {
        e.preventDefault();
        setOpen((prev) => !prev);
        return;
      }

      if (e.key === "/") {
        e.preventDefault();
        const searchInput = document.querySelector(
          'input[type="search"], input[placeholder*="search" i], input[placeholder*="Search" i]'
        ) as HTMLElement | null;
        if (searchInput) {
          searchInput.focus();
        } else {
          addToast("Search bar not available on this page", "info");
        }
        return;
      }

      if (e.key === "t" || e.key === "T") {
        e.preventDefault();
        toggleTheme();
        addToast(`Switched to ${theme === "dark" ? "light" : "dark"} mode`, "info");
        return;
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      clearSeqTimeout();
    };
  }, [open, sequence, navigate, addToast, toggleTheme, theme, resetSequence, startSequence, clearSeqTimeout]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          setOpen(false);
        }
      }}
    >
      <div
        ref={overlayRef}
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard shortcuts"
        className="w-full max-w-lg rounded-xl bg-surface border border-border shadow-2xl overflow-hidden"
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2 font-semibold text-primary">
            <Keyboard size={18} />
            Keyboard shortcuts
          </div>
          <button
            ref={closeBtnRef}
            onClick={() => setOpen(false)}
            className="p-1.5 rounded-md hover:bg-surface-alt transition-colors"
            aria-label="Close keyboard shortcuts"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            {shortcuts.map((s) => (
              <div key={s.keys} className="flex items-center gap-3 text-sm">
                <div className="flex-shrink-0 w-5 text-muted">{s.icon}</div>
                <div className="flex items-center gap-2 flex-1">
                  <kbd className="inline-flex items-center gap-0.5 px-2 py-1 rounded-md bg-surface-alt border border-border text-xs font-mono font-medium text-primary min-w-[2rem] justify-center">
                    {s.keys.split(" ").map((part, idx) => (
                      <span key={idx} className="flex items-center gap-0.5">
                        {idx > 0 && <ChevronRight size={10} className="text-muted" />}
                        {part}
                      </span>
                    ))}
                  </kbd>
                  <span className="text-muted truncate">{s.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="px-5 py-3 border-t border-border bg-surface-alt/50 text-xs text-muted text-center">
          Press <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border font-mono">?</kbd> to toggle this help anytime.
        </div>
      </div>
    </div>
  );
}
