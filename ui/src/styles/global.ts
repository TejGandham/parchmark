// Global styles
// Migrated from base/global.css

export const globalStyles = {
  global: {
    // Base layout - Full height
    'html, body, #root': {
      height: '100%',
      margin: 0,
      padding: 0,
    },

    // Body styling - Theme-aware
    body: {
      bg: 'bg.canvas',
      color: 'text.primary',
      fontFamily: 'body',
      fontSize: 'md',
      lineHeight: 'relaxed',
      transition: 'background-color 0.2s, color 0.2s',
    },

    // Placeholder text color
    '*::placeholder': {
      color: 'text.muted',
    },

    // Border color for all elements
    '*, *::before, *::after': {
      borderColor: 'border.default',
    },

    // Transition class for note animations
    '.note-transition': {
      transition: 'all 0.3s ease-in-out',
    },
  },
};
