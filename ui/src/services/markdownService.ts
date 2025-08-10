/**
 * Markdown processing service
 * Central location for all markdown-related utilities
 */

/**
 * Extracts the title from markdown content
 * Looks for the first H1 heading (# Title)
 */
export const extractTitleFromMarkdown = (content: string): string => {
  const titleMatch = content.match(/^#\s+(.+)$/m);
  return titleMatch ? titleMatch[1].trim() : 'Untitled Note';
};

/**
 * Formats note content to ensure proper structure
 * Ensures content has proper spacing and formatting
 */
export const formatNoteContent = (content: string): string => {
  const cleanedContent = content.trim();
  const title = extractTitleFromMarkdown(cleanedContent);

  // If content is only a title, ensure it has spacing for editing
  return cleanedContent === `# ${title}` ? `# ${title}\n\n` : cleanedContent;
};

/**
 * Removes the H1 title heading from markdown content
 * Used to avoid duplicating the title in rendered content
 */
export const removeH1FromContent = (content: string): string => {
  return content.replace(/^#\s+(.+)($|\n)/, '').trim();
};

/**
 * Creates a new empty note content template
 */
export const createEmptyNoteContent = (title: string = 'New Note'): string => {
  return `# ${title}\n\n`;
};
