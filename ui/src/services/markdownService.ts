/**
 * Markdown processing service
 * Central location for all markdown-related utilities
 * Now using the shared MarkdownService class for consistency
 */

import { markdownService } from '../utils/markdown';

/**
 * Extracts the title from markdown content
 * Looks for the first H1 heading (# Title)
 */
export const extractTitleFromMarkdown = (content: string): string => {
  return markdownService.extractTitle(content);
};

/**
 * Formats note content to ensure proper structure
 * Ensures content has proper spacing and formatting
 */
export const formatNoteContent = (content: string): string => {
  return markdownService.formatContent(content);
};

/**
 * Removes the H1 title heading from markdown content
 * Used to avoid duplicating the title in rendered content
 */
export const removeH1FromContent = (content: string): string => {
  return markdownService.removeH1(content);
};

/**
 * Creates a new empty note content template
 */
export const createEmptyNoteContent = (title: string = 'New Note'): string => {
  return markdownService.createEmptyNote(title);
};
