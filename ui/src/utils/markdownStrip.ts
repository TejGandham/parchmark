/**
 * Strip markdown syntax to plain text using regex-based approach.
 */
export function stripMarkdownToPlainText(markdown: string): string {
  if (!markdown) return '';

  let text = markdown;

  // Fenced code blocks (before inline code)
  text = text.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/~~~[\s\S]*?~~~/g, '');

  // Images (before links — both use [...](...))
  text = text.replace(/!\[([^\]]*)\]\(.+?\)/g, '$1');

  // Links
  text = text.replace(/\[([^\]]*)\]\(.+?\)/g, '$1');

  // HTML tags
  text = text.replace(/<[^>]+>/g, '');

  // Headings
  text = text.replace(/^#{1,6}\s+/gm, '');

  // Bold/italic
  text = text.replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1');
  text = text.replace(/_{1,3}([^_]+)_{1,3}/g, '$1');

  // Strikethrough
  text = text.replace(/~~([^~]+)~~/g, '$1');

  // Inline code
  text = text.replace(/`([^`]+)`/g, '$1');

  // Blockquotes
  text = text.replace(/^>\s?/gm, '');

  // Horizontal rules
  text = text.replace(/^([-*_=])\1{2,}$/gm, '');

  // Task list markers
  text = text.replace(/^(\s*)[-*+]\s+\[[ xX]\]\s*/gm, '$1');

  // Unordered list markers
  text = text.replace(/^(\s*)[-*+]\s+/gm, '$1');

  // Ordered list markers
  text = text.replace(/^(\s*)\d+\.\s+/gm, '$1');

  // Table formatting
  text = text.replace(/\|/g, ' ');
  text = text.replace(/^[\s-:|]+$/gm, '');

  // Collapse whitespace
  text = text.replace(/\n{2,}/g, ' ');
  text = text.replace(/\n/g, ' ');
  text = text.replace(/\s{2,}/g, ' ');

  return text.trim();
}

/**
 * Get a content preview: strip markdown, remove H1 title, truncate.
 */
export function getContentPreview(
  content: string,
  maxLength: number = 120
): string {
  if (!content) return '';

  // Remove first H1 line
  const withoutH1 = content.replace(/^#\s+[^\n]*\n?/, '');

  const plain = stripMarkdownToPlainText(withoutH1);

  if (plain.length <= maxLength) return plain;
  return plain.slice(0, maxLength).trimEnd() + '...';
}

/**
 * Count words from plain text content.
 */
export function getWordCount(content: string): number {
  const plain = stripMarkdownToPlainText(content);
  if (!plain) return 0;
  return plain.split(/\s+/).filter(Boolean).length;
}

/**
 * Estimate reading time in minutes (200 WPM, minimum 1 minute).
 */
export function getReadingTime(wordCount: number): number {
  if (wordCount <= 0) return 1;
  return Math.ceil(wordCount / 200);
}
