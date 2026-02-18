/**
 * Markdown stripping utilities for plain text extraction and content analysis
 * Used for previews, word counts, and reading time estimates
 */

/**
 * Strip all markdown syntax from text, returning plain text.
 * Strips: headings, bold, italic, links, images, code blocks,
 * blockquotes, horizontal rules, HTML tags, task lists, tables, strikethrough
 */
export function stripMarkdownToPlainText(markdown: string): string {
  let text = markdown;

  text = text.replace(/<[^>]*>/g, '');
  text = text.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/~~~[\s\S]*?~~~/g, '');
  text = text.replace(/^([-*_=])\1{2,}$/gm, '');
  text = text.replace(/^#+\s+/gm, '');
  text = text.replace(/\*\*(.+?)\*\*/g, '$1');
  text = text.replace(/__(.+?)__/g, '$1');
  text = text.replace(/\*(.+?)\*/g, '$1');
  text = text.replace(/_(.+?)_/g, '$1');
  text = text.replace(/~~(.+?)~~/g, '$1');
  text = text.replace(/`(.+?)`/g, '$1');
  text = text.replace(/!\[([^\]]*)\]\(.+?\)/g, '$1');
  text = text.replace(/\[(.+?)\]\(.+?\)/g, '$1');
  text = text.replace(/^>\s+/gm, '');
  text = text.replace(/^-\s+\[[xX ]\]\s+/gm, '');
  text = text.replace(/\|/g, '');
  text = text.replace(/\n\n+/g, '\n');
  text = text.replace(/[ \t]+/g, ' ');

  return text.trim();
}

/**
 * Get a plain text content preview from markdown content.
 * - Strips markdown syntax
 * - Removes the first H1 heading (title line) to avoid duplication
 * - Collapses multiple whitespace/newlines
 * - Truncates to maxLength chars with "..." if needed
 * Default maxLength: 120
 */
export function getContentPreview(content: string, maxLength: number = 120): string {
  let text = content.replace(/^#\s+(.+)($|\n)/m, '');
  text = stripMarkdownToPlainText(text);
  text = text.replace(/\s+/g, ' ').trim();

  if (text.length > maxLength) {
    return text.substring(0, maxLength) + '...';
  }

  return text;
}

/**
 * Count words in plain text (whitespace-splitting, English-centric)
 */
export function getWordCount(content: string): number {
  const text = stripMarkdownToPlainText(content);
  if (!text.trim()) return 0;
  return text.trim().split(/\s+/).length;
}

/**
 * Estimate reading time in minutes.
 * Uses 200 words per minute reading speed.
 * Minimum 1 minute.
 */
export function getReadingTime(wordCount: number): number {
  const readingSpeed = 200;
  const minutes = Math.ceil(wordCount / readingSpeed);
  return Math.max(1, minutes);
}
