import { describe, it, expect } from 'vitest';
import { MarkdownService, markdownService } from '../../utils/markdown';

describe('MarkdownService', () => {
  describe('extractTitle', () => {
    it('should extract title from H1 heading', () => {
      const content = '# Test Title\n\nSome content';
      expect(markdownService.extractTitle(content)).toBe('Test Title');
    });

    it('should return default title when no H1 heading exists', () => {
      const content = '## H2 Heading\n\nContent';
      expect(markdownService.extractTitle(content)).toBe('Untitled Note');
    });

    it('should trim whitespace from extracted title', () => {
      const content = '#   Title with spaces   \n\nContent';
      expect(markdownService.extractTitle(content)).toBe('Title with spaces');
    });

    it('should handle empty content', () => {
      expect(markdownService.extractTitle('')).toBe('Untitled Note');
    });

    it('should extract first H1 when multiple exist', () => {
      const content = '# First Title\n\n# Second Title';
      expect(markdownService.extractTitle(content)).toBe('First Title');
    });
  });

  describe('formatContent', () => {
    it('should preserve content with title and body', () => {
      const content = '# Title\n\nBody content';
      expect(markdownService.formatContent(content)).toBe(content);
    });

    it('should add spacing when content is title-only', () => {
      const content = '# Title';
      expect(markdownService.formatContent(content)).toBe('# Title\n\n');
    });

    it('should trim whitespace', () => {
      const content = '  \n# Title\n\nContent  \n  ';
      expect(markdownService.formatContent(content)).toBe('# Title\n\nContent');
    });

    it('should handle empty content', () => {
      expect(markdownService.formatContent('')).toBe('');
    });
  });

  describe('removeH1', () => {
    it('should remove H1 heading from content', () => {
      const content = '# Title\n\nBody content';
      expect(markdownService.removeH1(content)).toBe('Body content');
    });

    it('should remove H1 heading without extra blank lines', () => {
      const content = '# Title\nBody content';
      expect(markdownService.removeH1(content)).toBe('Body content');
    });

    it('should handle content with only H1', () => {
      const content = '# Title';
      expect(markdownService.removeH1(content)).toBe('');
    });

    it('should preserve content when no H1 exists', () => {
      const content = 'Body content\n\n## H2 heading';
      expect(markdownService.removeH1(content)).toBe(
        'Body content\n\n## H2 heading'
      );
    });

    it('should remove only the first H1', () => {
      const content = '# First Title\n\nContent\n\n# Second Title';
      expect(markdownService.removeH1(content)).toBe(
        'Content\n\n# Second Title'
      );
    });

    it('should handle H1 with special characters', () => {
      const content = '# Title @#$%\n\nBody';
      expect(markdownService.removeH1(content)).toBe('Body');
    });

    it('should handle empty content', () => {
      expect(markdownService.removeH1('')).toBe('');
    });
  });

  describe('createEmptyNote', () => {
    it('should create note with default title', () => {
      expect(markdownService.createEmptyNote()).toBe('# New Note\n\n');
    });

    it('should create note with custom title', () => {
      expect(markdownService.createEmptyNote('My Custom Title')).toBe(
        '# My Custom Title\n\n'
      );
    });

    it('should handle empty string title', () => {
      expect(markdownService.createEmptyNote('')).toBe('# \n\n');
    });

    it('should handle title with special characters', () => {
      expect(markdownService.createEmptyNote('Title @#$%')).toBe(
        '# Title @#$%\n\n'
      );
    });

    it('should handle title with unicode', () => {
      expect(markdownService.createEmptyNote('标题 🚀')).toBe('# 标题 🚀\n\n');
    });
  });

  describe('MarkdownService class instantiation', () => {
    it('should allow creating new instances', () => {
      const service = new MarkdownService();
      expect(service.extractTitle('# Test')).toBe('Test');
    });

    it('should have singleton instance', () => {
      expect(markdownService).toBeInstanceOf(MarkdownService);
    });
  });

  describe('Integration tests', () => {
    it('should maintain consistency across extract and format cycle', () => {
      const content = '# Test Title\n\nContent';
      const title = markdownService.extractTitle(content);
      const formatted = markdownService.formatContent(content);
      const titleAgain = markdownService.extractTitle(formatted);

      expect(title).toBe(titleAgain);
      expect(formatted).toBe(content);
    });

    it('should work with createEmptyNote and extractTitle', () => {
      const title = 'Test Note';
      const content = markdownService.createEmptyNote(title);
      const extractedTitle = markdownService.extractTitle(content);

      expect(extractedTitle).toBe(title);
    });

    it('should properly remove H1 and preserve remaining content', () => {
      const content = '# Title\n\n## Subtitle\n\nBody content';
      const withoutH1 = markdownService.removeH1(content);
      expect(withoutH1).toBe('## Subtitle\n\nBody content');
      expect(withoutH1).not.toContain('# Title');
    });
  });
});
