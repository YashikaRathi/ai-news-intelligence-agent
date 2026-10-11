import React, { useEffect, useState } from 'react';
import { NotificationItem, NotificationPreference } from '../types';
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  getNotificationPreferences,
  updateNotificationPreferences,
} from '../services/api';
import { formatRelativeTime, formatISTDateTime } from '../utils/time';
import {
  Bell,
  Check,
  CheckCheck,
  X,
  Settings,
  Sparkles,
  Layers,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStory?: (storyId: string) => void;
  onUnreadCountChange?: (count: number) => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  isOpen,
  onClose,
  onSelectStory,
  onUnreadCountChange,
}) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [showPreferences, setShowPreferences] = useState<boolean>(false);
  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [savingPrefs, setSavingPrefs] = useState<boolean>(false);

  const loadNotifs = async () => {
    try {
      setLoading(true);
      const data = await getNotifications();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
      if (onUnreadCountChange) onUnreadCountChange(data.unread_count || 0);
    } catch (err) {
      console.warn('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPrefs = async () => {
    try {
      const pref = await getNotificationPreferences();
      setPreferences(pref);
    } catch (err) {
      console.warn('Failed to load preferences:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadNotifs();
      loadPrefs();
    }
  }, [isOpen]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
      if (onUnreadCountChange) onUnreadCountChange(Math.max(0, unreadCount - 1));
    } catch (err) {
      console.warn('Failed to mark read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
      if (onUnreadCountChange) onUnreadCountChange(0);
    } catch (err) {
      console.warn('Failed to mark all read:', err);
    }
  };

  const handleTogglePrefCategory = async (cat: string) => {
    if (!preferences) return;
    setSavingPrefs(true);
    const current = new Set(preferences.categories_enabled);
    if (current.has(cat)) current.delete(cat);
    else current.add(cat);

    try {
      const updated = await updateNotificationPreferences({
        categories_enabled: Array.from(current),
      });
      setPreferences(updated);
    } catch (err) {
      console.warn('Failed to update preference:', err);
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleToggleMasterEnabled = async () => {
    if (!preferences) return;
    setSavingPrefs(true);
    try {
      const updated = await updateNotificationPreferences({
        notifications_enabled: !preferences.notifications_enabled,
      });
      setPreferences(updated);
    } catch (err) {
      console.warn('Failed to toggle notifications:', err);
    } finally {
      setSavingPrefs(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end bg-black/40 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-[#E2E8F0] animate-in slide-in-from-right duration-200">
        {/* Top Header */}
        <div className="p-4 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8FAFC]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[#EFF6FF] text-[#2563EB]">
              <Bell className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-[#0F172A]">Notifications</h3>
              <span className="text-[11px] text-[#64748B] font-medium">
                {unreadCount > 0 ? `${unreadCount} unread update(s)` : 'All caught up'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowPreferences(!showPreferences)}
              className={`p-1.5 rounded-lg border text-xs font-semibold transition-colors ${
                showPreferences
                  ? 'bg-[#EFF6FF] text-[#2563EB] border-[#60A5FA]'
                  : 'bg-white hover:bg-slate-100 text-[#64748B] border-[#E2E8F0]'
              }`}
              title="Notification preferences"
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-[#64748B] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Preferences Toggle Drawer */}
        {showPreferences && preferences && (
          <div className="p-4 bg-slate-50 border-b border-[#E2E8F0] space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#0F172A]">In-App Notification Settings</span>
              <button
                onClick={handleToggleMasterEnabled}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preferences.notifications_enabled
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-rose-100 text-rose-800 border border-rose-300'
                }`}
              >
                {preferences.notifications_enabled ? 'Enabled' : 'Paused'}
              </button>
            </div>

            <p className="text-[11px] text-[#64748B]">
              Configure which news alerts and verification updates trigger persistent notifications:
            </p>

            <div className="space-y-1.5">
              {[
                { id: 'verification_change', label: 'Fact-Check Verification Updates' },
                { id: 'contradiction_alert', label: 'Cross-Source Contradiction Alerts' },
                { id: 'topic_alert', label: 'Followed Topic Articles' },
                { id: 'story_update', label: 'Followed Story Coverage' },
              ].map((item) => {
                const isChecked = preferences.categories_enabled.includes(item.id);
                return (
                  <label key={item.id} className="flex items-center gap-2 cursor-pointer font-medium text-[#334155]">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      disabled={savingPrefs || !preferences.notifications_enabled}
                      onChange={() => handleTogglePrefCategory(item.id)}
                      className="rounded text-[#2563EB] focus:ring-[#2563EB]"
                    />
                    <span>{item.label}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        {/* Action Bar */}
        <div className="px-4 py-2 border-b border-[#E2E8F0] flex items-center justify-between text-xs bg-white">
          <span className="text-[11px] text-[#64748B] font-semibold">
            {notifications.length} Total Alerts
          </span>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="text-[#2563EB] hover:text-[#1D4ED8] font-bold flex items-center gap-1 text-[11px]"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>Mark all as read</span>
            </button>
          )}
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto divide-y divide-[#E2E8F0]">
          {loading ? (
            <div className="py-12 text-center text-xs text-[#64748B]">Loading notifications...</div>
          ) : notifications.length === 0 ? (
            <div className="py-16 text-center space-y-2 px-6">
              <Bell className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-xs font-bold text-[#0F172A]">No notifications yet</p>
              <p className="text-[11px] text-[#64748B]">
                You will be notified when new topic stories, fact-check changes, or reporting contradictions are detected.
              </p>
            </div>
          ) : (
            notifications.map((item) => {
              const getIcon = () => {
                switch (item.event_type) {
                  case 'verification_change':
                    return <ShieldCheck className="w-4 h-4 text-emerald-600" />;
                  case 'contradiction_alert':
                    return <AlertTriangle className="w-4 h-4 text-orange-600" />;
                  case 'topic_alert':
                    return <Sparkles className="w-4 h-4 text-blue-600" />;
                  default:
                    return <Layers className="w-4 h-4 text-slate-500" />;
                }
              };

              return (
                <div
                  key={item.id}
                  className={`p-4 transition-colors flex items-start gap-3 group ${
                    item.is_read ? 'bg-white hover:bg-slate-50/80' : 'bg-[#EFF6FF]/40 hover:bg-[#EFF6FF]/60'
                  }`}
                >
                  <div className="p-2 rounded-lg bg-white border border-[#E2E8F0] shrink-0 mt-0.5 shadow-2xs">
                    {getIcon()}
                  </div>

                  <div className="flex-1 space-y-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-bold text-[#0F172A] truncate">
                        {item.title}
                      </span>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-[#2563EB] shrink-0" />
                      )}
                    </div>

                    <p className="text-xs text-[#475569] leading-relaxed line-clamp-3">
                      {item.message}
                    </p>

                    <div className="flex items-center justify-between pt-1 text-[10px] text-[#64748B]">
                      <span title={formatISTDateTime(item.created_at)}>
                        {formatRelativeTime(item.created_at)}
                      </span>

                      <div className="flex items-center gap-2">
                        {item.story_id && onSelectStory && (
                          <button
                            onClick={() => {
                              onSelectStory(item.story_id!);
                              onClose();
                            }}
                            className="font-bold text-[#2563EB] hover:underline flex items-center gap-0.5"
                          >
                            <span>Open Story</span>
                            <ExternalLink className="w-3 h-3" />
                          </button>
                        )}
                        {!item.is_read && (
                          <button
                            onClick={() => handleMarkRead(item.id)}
                            className="text-[#64748B] hover:text-[#0F172A] p-0.5"
                            title="Mark as read"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
