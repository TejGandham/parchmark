const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;

/**
 * Format a date string into a compact relative time.
 * Returns: "5m", "2h", "1d", "2w", "Jan 15"
 */
export const formatCompactTime = (dateStr: string): string => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  if (diffMs < 0) return 'now';

  if (diffMs < MINUTE) return 'now';

  const diffMins = Math.floor(diffMs / MINUTE);
  if (diffMins < 60) return `${diffMins}m`;

  const diffHours = Math.floor(diffMs / HOUR);
  if (diffHours < 24) return `${diffHours}h`;

  const diffDays = Math.floor(diffMs / DAY);
  if (diffDays < 7) return `${diffDays}d`;

  const diffWeeks = Math.floor(diffMs / WEEK);
  if (diffWeeks < 4) return `${diffWeeks}w`;

  // Older than 4 weeks: "Jan 15"
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};
