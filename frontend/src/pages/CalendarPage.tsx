import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  Trash2,
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  AlignLeft,
  Save,
  Loader2,
} from "lucide-react";

interface CalendarEvent {
  id: string;
  account_id: string;
  title: string;
  description: string | null;
  start_at: string;
  end_at: string | null;
  all_day: boolean;
  location: string | null;
  recurrence_rule: string | null;
  created_at: string;
  updated_at: string;
}

function getMonthStart(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function getMonthEnd(d: Date) {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59, 999);
}

function startOfWeek(d: Date) {
  const day = d.getDay();
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() - day);
}

function addDays(d: Date, n: number) {
  const copy = new Date(d);
  copy.setDate(copy.getDate() + n);
  return copy;
}

function isSameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function formatDateInput(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function parseDateInput(v: string) {
  return new Date(v);
}

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function CalendarPage() {
  const { addToast } = useToast();
  const [today] = useState(() => new Date());
  const [currentMonth, setCurrentMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    start_at: formatDateInput(today),
    end_at: "",
    all_day: false,
    location: "",
    recurrence_rule: "",
  });
  const [saving, setSaving] = useState(false);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const start = getMonthStart(currentMonth).toISOString();
      const end = getMonthEnd(currentMonth).toISOString();
      const res = await api.get<CalendarEvent[]>("/calendar/events", {
        params: { start, end },
      });
      setEvents(res.data);
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to load events", "error");
    } finally {
      setLoading(false);
    }
  }, [currentMonth, addToast]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const openCreate = (date: Date) => {
    setModalMode("create");
    setSelectedEvent(null);
    const start = new Date(date);
    start.setHours(9, 0, 0, 0);
    const end = new Date(date);
    end.setHours(10, 0, 0, 0);
    setForm({
      title: "",
      description: "",
      start_at: formatDateInput(start),
      end_at: formatDateInput(end),
      all_day: false,
      location: "",
      recurrence_rule: "",
    });
    setModalOpen(true);
  };

  const openEdit = (event: CalendarEvent) => {
    setModalMode("edit");
    setSelectedEvent(event);
    setForm({
      title: event.title,
      description: event.description || "",
      start_at: formatDateInput(new Date(event.start_at)),
      end_at: event.end_at ? formatDateInput(new Date(event.end_at)) : "",
      all_day: event.all_day,
      location: event.location || "",
      recurrence_rule: event.recurrence_rule || "",
    });
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload: any = {
        title: form.title,
        start_at: parseDateInput(form.start_at).toISOString(),
        all_day: form.all_day,
      };
      if (form.description) payload.description = form.description;
      if (form.end_at) payload.end_at = parseDateInput(form.end_at).toISOString();
      if (form.location) payload.location = form.location;
      if (form.recurrence_rule) payload.recurrence_rule = form.recurrence_rule;

      if (modalMode === "create") {
        await api.post("/calendar/events", payload);
        addToast("Event created", "success");
      } else if (selectedEvent) {
        await api.patch(`/calendar/events/${selectedEvent.id}`, payload);
        addToast("Event updated", "success");
      }
      setModalOpen(false);
      await loadEvents();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to save event", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedEvent) return;
    if (!confirm("Delete this event?")) return;
    try {
      await api.delete(`/calendar/events/${selectedEvent.id}`);
      addToast("Event deleted", "success");
      setModalOpen(false);
      await loadEvents();
    } catch (err: any) {
      addToast(err?.response?.data?.detail || "Failed to delete event", "error");
    }
  };

  const monthStart = getMonthStart(currentMonth);
  const monthEnd = getMonthEnd(currentMonth);
  const calendarStart = startOfWeek(monthStart);
  const days: Date[] = [];
  for (let i = 0; i < 42; i++) {
    days.push(addDays(calendarStart, i));
  }

  const prevMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  const nextMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));

  const monthLabel = currentMonth.toLocaleString("default", { month: "long", year: "numeric" });

  const eventsForDay = (date: Date) =>
    events.filter((ev) => {
      const s = new Date(ev.start_at);
      return isSameDay(s, date);
    });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Calendar</h1>
          <p className="text-sm text-muted">Manage your schedule.</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary flex items-center gap-1" onClick={prevMonth}>
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm font-semibold min-w-[8rem] text-center">{monthLabel}</span>
          <button className="btn-secondary flex items-center gap-1" onClick={nextMonth}>
            <ChevronRight size={16} />
          </button>
          <button className="btn-primary flex items-center gap-2 ml-2" onClick={() => openCreate(today)}>
            <Plus size={16} /> Add event
          </button>
        </div>
      </div>

      {loading ? (
        <Loading />
      ) : (
        <div className="card p-4">
          <div className="grid grid-cols-7 gap-1">
            {WEEKDAYS.map((wd) => (
              <div key={wd} className="text-center text-xs font-semibold text-muted py-2">
                {wd}
              </div>
            ))}
            {days.map((day, idx) => {
              const inMonth = day >= monthStart && day <= monthEnd;
              const isToday = isSameDay(day, today);
              const dayEvents = eventsForDay(day);
              return (
                <div
                  key={idx}
                  className={`min-h-[6rem] border border-border rounded-lg p-1 cursor-pointer hover:bg-surface-alt transition-colors ${
                    inMonth ? "bg-surface" : "bg-surface-alt/50 opacity-60"
                  }`}
                  onClick={() => openCreate(day)}
                >
                  <div className="flex items-center justify-between px-1">
                    <span className={`text-xs font-medium ${isToday ? "text-accent font-bold" : ""}`}>
                      {day.getDate()}
                    </span>
                    {isToday && <span className="w-1.5 h-1.5 rounded-full bg-accent" />}
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {dayEvents.slice(0, 3).map((ev) => (
                      <div
                        key={ev.id}
                        className="text-[10px] leading-tight truncate px-1 py-0.5 rounded bg-accent/10 text-accent cursor-pointer"
                        onClick={(e) => {
                          e.stopPropagation();
                          openEdit(ev);
                        }}
                        title={ev.title}
                      >
                        {ev.all_day ? "• " : ""}
                        {ev.title}
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-[10px] text-muted px-1">+{dayEvents.length - 3} more</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h2 className="text-lg font-semibold">
                {modalMode === "create" ? "New Event" : "Edit Event"}
              </h2>
              <button className="text-muted hover:text-primary" onClick={() => setModalOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSave} className="px-5 py-4 space-y-4">
              <div>
                <label className="label flex items-center gap-1">
                  <CalendarIcon size={14} /> Title
                </label>
                <input
                  type="text"
                  className="input"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                />
              </div>
              <div className="flex items-center gap-3">
                <input
                  id="all_day"
                  type="checkbox"
                  className="h-4 w-4"
                  checked={form.all_day}
                  onChange={(e) => setForm({ ...form, all_day: e.target.checked })}
                />
                <label htmlFor="all_day" className="text-sm">All day</label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label flex items-center gap-1">
                    <Clock size={14} /> Start
                  </label>
                  <input
                    type="datetime-local"
                    className="input"
                    value={form.start_at}
                    onChange={(e) => setForm({ ...form, start_at: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label flex items-center gap-1">
                    <Clock size={14} /> End
                  </label>
                  <input
                    type="datetime-local"
                    className="input"
                    value={form.end_at}
                    onChange={(e) => setForm({ ...form, end_at: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="label flex items-center gap-1">
                  <MapPin size={14} /> Location
                </label>
                <input
                  type="text"
                  className="input"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                />
              </div>
              <div>
                <label className="label flex items-center gap-1">
                  <AlignLeft size={14} /> Description
                </label>
                <textarea
                  className="input min-h-[80px]"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
              <div className="flex items-center justify-between gap-2 pt-2">
                <div className="flex items-center gap-2">
                  {modalMode === "edit" && (
                    <button
                      type="button"
                      className="btn-danger flex items-center gap-2"
                      onClick={handleDelete}
                    >
                      <Trash2 size={16} /> Delete
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button type="button" className="btn-secondary" onClick={() => setModalOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary flex items-center gap-2" disabled={saving}>
                    {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                    Save
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
