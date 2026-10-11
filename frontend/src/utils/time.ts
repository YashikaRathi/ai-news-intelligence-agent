/**
 * Audited News Timestamp & Timezone Utility
 * 
 * Handles:
 * - ISO 8601 timestamps, explicit offsets, UTC Z suffixes
 * - Relative time calculations without double-conversion
 * - Clock drift protection (future timestamps show 'Just now', not negative time)
 * - India Standard Time (Asia/Kolkata, UTC+5:30) formatting
 * - Clear distinction for missing publication times ("Publication time unavailable")
 */

/**
 * Format relative time (e.g. 'Just now', '5 minutes ago', '2 hours ago', 'Yesterday', '3 days ago')
 * If older than 7 days, returns a formatted date 'MMM D, YYYY'.
 * If date is missing/empty, returns 'Publication time unavailable'.
 */
export function formatRelativeTime(dateString?: string | null): string {
  if (!dateString || typeof dateString !== 'string' || !dateString.trim()) {
    return 'Publication time unavailable';
  }

  const cleanDateStr = dateString.trim();
  // Ensure ISO format parseable by browser engine
  const parsedTime = Date.parse(cleanDateStr);
  if (isNaN(parsedTime)) {
    return 'Publication time unavailable';
  }

  const now = Date.now();
  const diffSeconds = Math.floor((now - parsedTime) / 1000);

  // If timestamp is slightly in the future due to clock drift (up to 5 mins ahead), clamp to 'Just now'
  if (diffSeconds < 60) {
    return 'Just now';
  }

  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? 'minute' : 'minutes'} ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) {
    return 'Yesterday';
  }
  if (diffDays < 7) {
    return `${diffDays} days ago`;
  }

  // Format as readable date for older items
  try {
    return new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(parsedTime));
  } catch {
    return new Date(parsedTime).toLocaleDateString();
  }
}

/**
 * Format timestamp accurately in India Standard Time (Asia/Kolkata, UTC+05:30).
 * Does not manually add/subtract 5:30 to prevent double-conversion.
 */
export function formatISTDateTime(dateString?: string | null): string {
  if (!dateString || !dateString.trim()) {
    return 'Unavailable';
  }

  const parsedTime = Date.parse(dateString.trim());
  if (isNaN(parsedTime)) {
    return 'Unavailable';
  }

  try {
    const formatter = new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
    return `${formatter.format(new Date(parsedTime))} IST`;
  } catch {
    return `${new Date(parsedTime).toLocaleString()} (Local)`;
  }
}

/**
 * Returns full tooltip text with exact IST datetime and UTC ISO string for transparency.
 */
export function getTimestampTooltip(dateString?: string | null, label = 'Published'): string {
  if (!dateString || !dateString.trim()) {
    return `${label} time unavailable`;
  }
  const ist = formatISTDateTime(dateString);
  return `${label}: ${ist} (UTC: ${dateString})`;
}
