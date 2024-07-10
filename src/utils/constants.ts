import { Note } from '../types';
import { colors } from '../styles/tokens';

export const DEFAULT_NOTES: Note[] = [
  {
    id: '1',
    title: 'Welcome to ParchMark',
    content:
      '# Welcome to ParchMark\n\nThis is a simple yet powerful note-taking application inspired by ancient papyrus and modern markdown. Here are some features:\n\n- **Markdown support**\n- Dark mode support\n- Clean, minimal UI\n\nFeel free to edit this note or create a new one!',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    title: 'Getting Started',
    content:
      '# Getting Started\n\n1. Create new notes using the + button\n2. Edit notes in markdown\n3. Toggle between edit and preview mode\n4. Use the sidebar to navigate between notes',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

export const COLORS = {
  primaryColor: colors.primary.main,
  primaryLight: colors.primary.light,
  complementaryColor: colors.complementary,
  bgColor: colors.background.light,
  sidebarBgColor: colors.ui.sidebar,
  headingColor: colors.primary.main,
  textColor: 'gray.700',
};

// Utility functions for content manipulation
export const extractTitleFromMarkdown = (content: string): string => {
  const titleMatch = content.match(/^#\s+(.+)$/m);
  return titleMatch ? titleMatch[1].trim() : 'Untitled Note';
};

export const formatNoteContent = (content: string): string => {
  const cleanedContent = content.trim();
  const title = extractTitleFromMarkdown(cleanedContent);

  // If content is only a title, ensure it has spacing for editing
  return cleanedContent === `# ${title}` ? `# ${title}\n\n` : cleanedContent;
};
