import type { NoteMock } from "./mockNotes";

const day = 86_400_000;

export interface TagCount {
  tag: string;
  count: number;
}

export interface TimeGroup {
  key: "today" | "yesterday" | "week" | "earlier";
  label: string;
  notes: NoteMock[];
}

export function extractTitle(markdown: string): string {
  const match = (markdown || "").match(/^\s*#\s+(.+?)\s*$/m);
  return match ? match[1].trim() : "Untitled";
}

export function stripTitle(markdown: string): string {
  return (markdown || "")
    .replace(/^\s*#\s+.+?(\r?\n|$)/, "")
    .replace(/^\s+/, "");
}

export function plainPreview(markdown: string): string {
  return stripTitle(markdown)
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^[>#\-*+]\s?/gm, "")
    .replace(/^\s*\d+\.\s/gm, "")
    .replace(/[*_~|]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function wordCount(markdown: string): number {
  const preview = plainPreview(markdown);
  return preview ? preview.split(/\s+/).length : 0;
}

export function readingTime(markdown: string): number {
  return Math.max(1, Math.round(wordCount(markdown) / 200));
}

export function allTags(notes: NoteMock[]): TagCount[] {
  const counts = new Map<string, number>();

  notes.forEach((note) => {
    note.tags.forEach((tag) => counts.set(tag, (counts.get(tag) ?? 0) + 1));
  });

  return Array.from(counts, ([tag, count]) => ({ tag, count })).sort(
    (left, right) =>
      right.count - left.count || left.tag.localeCompare(right.tag),
  );
}

export function relTime(timestamp: number, now = Date.now()): string {
  const seconds = Math.floor((now - timestamp) / 1000);
  if (seconds < 60) return "just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  if (days === 1) return "yesterday";
  if (days < 7) return `${days}d ago`;

  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `${weeks}w ago`;

  return new Date(timestamp).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function startOfToday(now = Date.now()): number {
  const date = new Date(now);
  date.setHours(0, 0, 0, 0);
  return date.getTime();
}

export function groupByTime(notes: NoteMock[], now = Date.now()): TimeGroup[] {
  const todayStart = startOfToday(now);
  const yesterdayStart = todayStart - day;
  const weekStart = todayStart - 7 * day;
  const buckets: TimeGroup[] = [
    { key: "today", label: "Today", notes: [] },
    { key: "yesterday", label: "Yesterday", notes: [] },
    { key: "week", label: "Earlier this week", notes: [] },
    { key: "earlier", label: "Earlier", notes: [] },
  ];

  notes.forEach((note) => {
    if (note.updatedAt >= todayStart) {
      buckets[0].notes.push(note);
    } else if (note.updatedAt >= yesterdayStart) {
      buckets[1].notes.push(note);
    } else if (note.updatedAt >= weekStart) {
      buckets[2].notes.push(note);
    } else {
      buckets[3].notes.push(note);
    }
  });

  return buckets.filter((bucket) => bucket.notes.length > 0);
}
