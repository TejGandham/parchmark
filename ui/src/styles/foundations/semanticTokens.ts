// Semantic tokens for theme-aware values
// Automatically adapt to light/dark mode

export const semanticTokens = {
  colors: {
    // Text colors
    'text.primary': {
      default: 'neutral.900',
      _dark: 'neutral.50',
    },
    'text.secondary': {
      default: 'neutral.600',
      _dark: 'neutral.400',
    },
    'text.muted': {
      default: 'neutral.500',
      _dark: 'neutral.500',
    },

    // Background colors
    'bg.canvas': {
      default: 'neutral.50',
      _dark: 'neutral.900',
    },
    'bg.surface': {
      default: 'white',
      _dark: 'neutral.800',
    },
    'bg.subtle': {
      default: 'neutral.100',
      _dark: 'neutral.700',
    },

    // Border colors
    'border.default': {
      default: 'neutral.200',
      _dark: 'neutral.600',
    },
    'border.emphasis': {
      default: 'primary.800',
      _dark: 'primary.400',
    },

    // Interactive states
    'interactive.hover': {
      default: 'neutral.100',
      _dark: 'neutral.700',
    },
    'interactive.active': {
      default: 'primary.50',
      _dark: 'primary.900',
    },
  },
};
