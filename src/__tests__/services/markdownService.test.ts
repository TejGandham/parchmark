import {
  extractTitleFromMarkdown,
  formatNoteContent,
  removeH1FromContent,
  createEmptyNoteContent,
} from '../../services/markdownService';

describe('Markdown Service', () => {
  describe('extractTitleFromMarkdown', () => {
    it('should extract the title from a markdown string with an H1', () => {
      const content = '# My Title\n\nSome content here';
      expect(extractTitleFromMarkdown(content)).toBe('My Title');
    });

    it('should return "Untitled Note" if no H1 heading is found', () => {
      const content = 'Some content without a heading';
      expect(extractTitleFromMarkdown(content)).toBe('Untitled Note');
    });

    it('should extract the first H1 if multiple H1s exist', () => {
      const content = '# First Title\n\nContent\n\n# Second Title';
      expect(extractTitleFromMarkdown(content)).toBe('First Title');
    });

    it('should handle H1 with special characters', () => {
      const content = '# Title with *bold* and _italic_';
      expect(extractTitleFromMarkdown(content)).toBe(
        'Title with *bold* and _italic_'
      );
    });

    it('should extract title when H1 is not the first line', () => {
      const content = '\n\n# My Title\n\nContent';
      expect(extractTitleFromMarkdown(content)).toBe('My Title');
    });
  });

  describe('formatNoteContent', () => {
    it('should clean up extra whitespace around content', () => {
      const content = '  # My Note  \n\nContent  ';
      expect(formatNoteContent(content)).toBe('# My Note  \n\nContent');
    });

    it('should add extra new lines if content is only a title', () => {
      const content = '# My Note';
      expect(formatNoteContent(content)).toBe('# My Note\n\n');
    });

    it('should not add extra new lines if content already has text after title', () => {
      const content = '# My Note\n\nThis has content';
      expect(formatNoteContent(content)).toBe('# My Note\n\nThis has content');
    });

    it('should handle content without title', () => {
      const content = 'Just some text';
      expect(formatNoteContent(content)).toBe('Just some text');
    });
  });

  describe('removeH1FromContent', () => {
    it('should remove the H1 heading from the content', () => {
      const content = '# My Title\n\nSome content here';
      expect(removeH1FromContent(content)).toBe('Some content here');
    });

    it('should return empty string if content only has H1', () => {
      const content = '# My Title';
      expect(removeH1FromContent(content)).toBe('');
    });

    it('should handle content without H1', () => {
      const content = 'Just some text';
      expect(removeH1FromContent(content)).toBe('Just some text');
    });

    it('should only remove the first H1', () => {
      const content = '# First Title\n\nContent\n\n# Second Title';
      expect(removeH1FromContent(content)).toBe('Content\n\n# Second Title');
    });

    it('should handle content with multiple newlines after H1', () => {
      const content = '# My Title\n\n\n\nSome content here';
      expect(removeH1FromContent(content)).toBe('Some content here');
    });
  });

  describe('createEmptyNoteContent', () => {
    it('should create empty note content with default title', () => {
      expect(createEmptyNoteContent()).toBe('# New Note\n\n');
    });

    it('should create empty note content with provided title', () => {
      expect(createEmptyNoteContent('Custom Title')).toBe('# Custom Title\n\n');
    });

    it('should handle special characters in title', () => {
      expect(createEmptyNoteContent('Title with *special* chars')).toBe(
        '# Title with *special* chars\n\n'
      );
    });
  });
});
