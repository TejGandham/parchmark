/**
 * Shared markdown processing utilities
 * This implementation mirrors the backend markdown service to ensure consistency
 */

export interface MarkdownProcessor {
  extractTitle(content: string): string;
  formatContent(content: string): string;
  removeH1(content: string): string;
  createEmptyNote(title?: string): string;
}

export class MarkdownService implements MarkdownProcessor {
  private static readonly H1_REGEX = /^#\s+(.+)$/m;
  private static readonly H1_REMOVE_REGEX = /^#\s+(.+)($|\n)/m;
  private static readonly DEFAULT_TITLE = 'Untitled Note';

  extractTitle(content: string): string {
    const match = content.match(MarkdownService.H1_REGEX);
    return match ? match[1].trim() : MarkdownService.DEFAULT_TITLE;
  }

  formatContent(content: string): string {
    const cleaned = content.trim();
    const title = this.extractTitle(cleaned);

    return cleaned === `# ${title}` ? `# ${title}\n\n` : cleaned;
  }

  removeH1(content: string): string {
    // JavaScript replace() without /g flag only replaces the first occurrence
    return content.replace(MarkdownService.H1_REMOVE_REGEX, '').trim();
  }

  createEmptyNote(title: string = 'New Note'): string {
    return `# ${title}\n\n`;
  }
}

// Export singleton instance for convenience
export const markdownService = new MarkdownService();

// Shared test cases to ensure parity with backend
export const markdownTestCases = [
  { input: '# Test\n\nContent', expectedTitle: 'Test' },
  { input: 'No heading', expectedTitle: 'Untitled Note' },
  { input: '## Not H1\n\nContent', expectedTitle: 'Untitled Note' },
  { input: '# Multiple\n\n# Headings', expectedTitle: 'Multiple' },
  { input: '# Title with spaces  ', expectedTitle: 'Title with spaces' },
  { input: '#NoSpace', expectedTitle: 'Untitled Note' },
  { input: '', expectedTitle: 'Untitled Note' },
];
