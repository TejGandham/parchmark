const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

/** "just now" | "5 minutes ago" | "yesterday" | "Jan 5" | "Jan 5, 2024" */
export const formatRelativeDate = (iso: string): string => {
  const date = new Date(iso);
  const now = new Date();
  const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSeconds < MINUTE) {
    return 'just now';
  }
  if (diffSeconds < HOUR) {
    return rtf.format(-Math.floor(diffSeconds / MINUTE), 'minute');
  }
  if (diffSeconds < DAY) {
    return rtf.format(-Math.floor(diffSeconds / HOUR), 'hour');
  }
  if (diffSeconds < WEEK) {
    return rtf.format(-Math.floor(diffSeconds / DAY), 'day');
  }

  return formatShortDate(iso);
};

/** "Jan 5" (same year) or "Jan 5, 2024" (different year) */
export const formatShortDate = (iso: string): string => {
  const date = new Date(iso);
  const now = new Date();
  const sameYear = date.getFullYear() === now.getFullYear();

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  });
};

/** "January 5, 2024 at 3:45 PM" */
export const formatFullDate = (iso: string): string => {
  const date = new Date(iso);
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

/** True when two timestamps differ by more than 60 seconds */
export const datesAreDifferent = (a: string, b: string): boolean => {
  return Math.abs(new Date(a).getTime() - new Date(b).getTime()) > 60 * 1000;
};
