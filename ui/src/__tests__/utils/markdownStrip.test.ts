import { describe, it, expect } from 'vitest';
import {
  stripMarkdownToPlainText,
  getContentPreview,
  getWordCount,
  getReadingTime,
} from '../../utils/markdownStrip';

describe('stripMarkdownToPlainText', () => {
  it('removes headings', () => {
    expect(stripMarkdownToPlainText('# Heading 1')).toBe('Heading 1');
    expect(stripMarkdownToPlainText('## Heading 2')).toBe('Heading 2');
    expect(stripMarkdownToPlainText('### Heading 3')).toBe('Heading 3');
  });

  it('removes bold markdown', () => {
    expect(stripMarkdownToPlainText('**bold text**')).toBe('bold text');
    expect(stripMarkdownToPlainText('__bold text__')).toBe('bold text');
  });

  it('removes italic markdown', () => {
    expect(stripMarkdownToPlainText('*italic text*')).toBe('italic text');
    expect(stripMarkdownToPlainText('_italic text_')).toBe('italic text');
  });

  it('removes links and keeps text', () => {
    expect(stripMarkdownToPlainText('[link text](https://example.com)')).toBe('link text');
    expect(stripMarkdownToPlainText('Check [this](http://example.com) out')).toBe('Check this out');
  });

  it('removes images and keeps alt text', () => {
    expect(stripMarkdownToPlainText('![alt text](image.png)')).toBe('alt text');
    expect(stripMarkdownToPlainText('![](image.png)')).toBe('');
  });

  it('removes fenced code blocks', () => {
    const codeBlock = '```\nconst x = 1;\n```';
    expect(stripMarkdownToPlainText(codeBlock)).toBe('');

    const tildeBlock = '~~~\ncode here\n~~~';
    expect(stripMarkdownToPlainText(tildeBlock)).toBe('');
  });

  it('removes inline code backticks', () => {
    expect(stripMarkdownToPlainText('Use `const x = 1` in code')).toBe('Use const x = 1 in code');
  });

  it('removes blockquotes', () => {
    expect(stripMarkdownToPlainText('> This is a quote')).toBe('This is a quote');
    expect(stripMarkdownToPlainText('> Quote line 1\n> Quote line 2')).toBe('Quote line 1\nQuote line 2');
  });

  it('removes horizontal rules', () => {
    expect(stripMarkdownToPlainText('---')).toBe('');
    expect(stripMarkdownToPlainText('=====')).toBe('');
    expect(stripMarkdownToPlainText('***')).toBe('');
  });

  it('removes HTML tags', () => {
    expect(stripMarkdownToPlainText('<div>content</div>')).toBe('content');
    expect(stripMarkdownToPlainText('<p>paragraph</p>')).toBe('paragraph');
  });

  it('removes task list markers', () => {
    expect(stripMarkdownToPlainText('- [ ] Unchecked task')).toBe('Unchecked task');
    expect(stripMarkdownToPlainText('- [x] Checked task')).toBe('Checked task');
    expect(stripMarkdownToPlainText('- [X] Checked task')).toBe('Checked task');
  });

  it('removes table pipes', () => {
    expect(stripMarkdownToPlainText('| Header 1 | Header 2 |')).toBe('Header 1 Header 2');
  });

  it('removes strikethrough', () => {
    expect(stripMarkdownToPlainText('~~strikethrough~~')).toBe('strikethrough');
  });

  it('handles complex markdown', () => {
    const complex = `# Title
    
**Bold** and *italic* text with [link](url) and ![image](img.png).

\`\`\`
code block
\`\`\`

> A quote

- [ ] Task item`;

    const result = stripMarkdownToPlainText(complex);
    expect(result).toContain('Title');
    expect(result).toContain('Bold');
    expect(result).toContain('italic');
    expect(result).toContain('link');
    expect(result).toContain('image');
    expect(result).toContain('quote');
    expect(result).toContain('Task item');
    expect(result).not.toContain('```');
    expect(result).not.toContain('**');
    expect(result).not.toContain('[');
  });

  it('collapses multiple whitespace', () => {
    expect(stripMarkdownToPlainText('text   with    spaces')).toBe('text with spaces');
    expect(stripMarkdownToPlainText('line1\n\n\nline2')).toBe('line1\nline2');
  });

  it('trims whitespace', () => {
    expect(stripMarkdownToPlainText('  text  ')).toBe('text');
    expect(stripMarkdownToPlainText('\n\ntext\n\n')).toBe('text');
  });

  it('handles empty string', () => {
    expect(stripMarkdownToPlainText('')).toBe('');
  });
});

describe('getContentPreview', () => {
  it('removes H1 heading', () => {
    const content = '# Title\n\nContent here';
    expect(getContentPreview(content)).toBe('Content here');
  });

  it('removes markdown syntax', () => {
    const content = '# Title\n\n**Bold** and *italic*';
    expect(getContentPreview(content)).toBe('Bold and italic');
  });

  it('truncates at default 120 chars', () => {
    const longContent = '# Title\n\n' + 'a'.repeat(150);
    const preview = getContentPreview(longContent);
    expect(preview.length).toBe(123); // 120 + '...'
    expect(preview.endsWith('...')).toBe(true);
  });

  it('respects custom maxLength', () => {
    const content = '# Title\n\n' + 'a'.repeat(100);
    const preview = getContentPreview(content, 50);
    expect(preview.length).toBe(53); // 50 + '...'
    expect(preview.endsWith('...')).toBe(true);
  });

  it('does not truncate short content', () => {
    const content = '# Title\n\nShort content';
    const preview = getContentPreview(content);
    expect(preview).toBe('Short content');
    expect(preview).not.toContain('...');
  });

  it('handles content with only H1', () => {
    const content = '# Title Only';
    const preview = getContentPreview(content);
    expect(preview).toBe('');
  });

  it('handles empty content', () => {
    expect(getContentPreview('')).toBe('');
  });

  it('collapses whitespace in preview', () => {
    const content = '# Title\n\nText   with    multiple    spaces';
    const preview = getContentPreview(content);
    expect(preview).toBe('Text with multiple spaces');
  });

  it('handles content without H1', () => {
    const content = 'No heading here\n\nJust content';
    const preview = getContentPreview(content);
    expect(preview).toBe('No heading here Just content');
  });

  it('truncates at word boundary when possible', () => {
    const content = '# Title\n\n' + 'word '.repeat(30);
    const preview = getContentPreview(content, 50);
    expect(preview.length).toBeLessThanOrEqual(53);
    expect(preview.endsWith('...')).toBe(true);
  });
});

describe('getWordCount', () => {
  it('counts words in plain text', () => {
    expect(getWordCount('one two three')).toBe(3);
  });

  it('counts words after stripping markdown', () => {
    expect(getWordCount('**bold** and *italic*')).toBe(3);
  });

  it('handles empty string', () => {
    expect(getWordCount('')).toBe(0);
  });

  it('handles whitespace-only string', () => {
    expect(getWordCount('   \n\n   ')).toBe(0);
  });

  it('counts words with multiple spaces', () => {
    expect(getWordCount('one   two   three')).toBe(3);
  });

  it('counts words with newlines', () => {
    expect(getWordCount('one\ntwo\nthree')).toBe(3);
  });

  it('counts words in markdown content', () => {
    const content = '# Title\n\nThis is a paragraph with five words.';
    expect(getWordCount(content)).toBe(8); // Title + 5 words + 2 more
  });

  it('counts words with mixed punctuation', () => {
    expect(getWordCount('hello, world! how are you?')).toBe(5);
  });
});

describe('getReadingTime', () => {
  it('returns 1 minute for 0 words', () => {
    expect(getReadingTime(0)).toBe(1);
  });

  it('returns 1 minute for 1-200 words', () => {
    expect(getReadingTime(1)).toBe(1);
    expect(getReadingTime(100)).toBe(1);
    expect(getReadingTime(200)).toBe(1);
  });

  it('returns 2 minutes for 201-400 words', () => {
    expect(getReadingTime(201)).toBe(2);
    expect(getReadingTime(300)).toBe(2);
    expect(getReadingTime(400)).toBe(2);
  });

  it('returns 3 minutes for 401-600 words', () => {
    expect(getReadingTime(401)).toBe(3);
    expect(getReadingTime(500)).toBe(3);
    expect(getReadingTime(600)).toBe(3);
  });

  it('rounds up fractional minutes', () => {
    expect(getReadingTime(210)).toBe(2); // 210/200 = 1.05, ceil = 2
    expect(getReadingTime(250)).toBe(2); // 250/200 = 1.25, ceil = 2
  });

  it('handles large word counts', () => {
    expect(getReadingTime(2000)).toBe(10);
    expect(getReadingTime(5000)).toBe(25);
  });
});
