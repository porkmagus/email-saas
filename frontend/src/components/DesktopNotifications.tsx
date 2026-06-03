import { useEffect, useState } from "react";
import { Bell, BellOff } from "lucide-react";

const STORAGE_KEY = "desktop_notifications_enabled";

export function getDesktopNotificationsEnabled(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

export function setDesktopNotificationsEnabled(enabled: boolean) {
  try {
    localStorage.setItem(STORAGE_KEY, String(enabled));
  } catch {
    // ignore
  }
}

export function getNotificationPermission(): NotificationPermission | "unsupported" {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  return Notification.permission;
}

export async function requestNotificationPermission(): Promise<NotificationPermission | "unsupported"> {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  if (Notification.permission === "granted") return "granted";
  try {
    const result = await Notification.requestPermission();
    return result;
  } catch {
    return "unsupported";
  }
}

export function showNotification(title: string, body: string) {
  if (typeof window === "undefined" || !("Notification" in window)) return;
  if (Notification.permission !== "granted") return;
  if (!getDesktopNotificationsEnabled()) return;
  try {
    new Notification(title, { body, icon: "/favicon.ico" });
  } catch {
    // ignore
  }
}

export function DesktopNotificationsToggle() {
  const [permission, setPermission] = useState<NotificationPermission | "unsupported">("default");
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    setPermission(getNotificationPermission());
    setEnabled(getDesktopNotificationsEnabled());
  }, []);

  const handleToggle = async () => {
    const perm = await requestNotificationPermission();
    setPermission(perm);
    if (perm === "granted") {
      const next = !enabled;
      setEnabled(next);
      setDesktopNotificationsEnabled(next);
      if (next) {
        showNotification("Desktop notifications enabled", "You will now receive notifications here.");
      }
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted">Permission:</span>
        <span
          className={`font-medium ${
            permission === "granted"
              ? "text-success"
              : permission === "denied"
              ? "text-danger"
              : "text-warning"
          }`}
        >
          {permission === "unsupported" ? "Not supported" : permission}
        </span>
      </div>
      <button
        className={`btn-primary flex items-center gap-2 text-sm ${
          enabled && permission === "granted" ? "" : "opacity-90"
        }`}
        onClick={handleToggle}
        disabled={permission === "unsupported"}
      >
        {enabled && permission === "granted" ? <Bell size={16} /> : <BellOff size={16} />}
        {enabled && permission === "granted" ? "Disable desktop notifications" : "Enable desktop notifications"}
      </button>
    </div>
  );
}
