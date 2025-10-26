// Shadow system for ParchMark
// Uses primary burgundy color (#580c24) for brand-aligned shadows

export const shadows = {
  // Base Shadows - Using primary color for subtle brand presence
  xs: '0 1px 2px rgba(88, 12, 36, 0.05)',
  sm: '0 2px 4px rgba(88, 12, 36, 0.08)',
  md: '0 4px 12px rgba(88, 12, 36, 0.12)',
  lg: '0 8px 24px rgba(88, 12, 36, 0.15)',
  xl: '0 16px 48px rgba(88, 12, 36, 0.18)',
  '2xl': '0 24px 64px rgba(88, 12, 36, 0.22)',

  // Inner Shadows - For inset/well effects
  inner: 'inset 0 2px 4px rgba(88, 12, 36, 0.06)',
  innerLg: 'inset 0 4px 8px rgba(88, 12, 36, 0.1)',

  // Colored Shadows - For emphasis and interaction
  primary: '0 8px 24px rgba(88, 12, 36, 0.35)',
  primarySm: '0 4px 12px rgba(88, 12, 36, 0.25)',
  success: '0 4px 12px rgba(42, 125, 64, 0.25)',
  error: '0 4px 12px rgba(244, 63, 94, 0.25)',

  // Specialized Shadows - For specific components
  sidebar: '3px 0 10px rgba(88, 12, 36, 0.05)',
  sidebarDark: '3px 0 15px rgba(0, 0, 0, 0.25)',
  card: '0 2px 8px rgba(88, 12, 36, 0.08)',
  cardHover: '0 8px 24px rgba(88, 12, 36, 0.15)',
  dropdown: '0 12px 32px rgba(88, 12, 36, 0.18)',

  // Focus States - For accessibility and interaction feedback
  outline: '0 0 0 3px rgba(88, 12, 36, 0.1)',
  outlineBlue: '0 0 0 3px rgba(59, 130, 246, 0.15)',

  // Chakra UI standard shadows (backward compatibility)
  none: 'none',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  'dark-lg':
    'rgba(0, 0, 0, 0.1) 0px 0px 0px 1px, rgba(0, 0, 0, 0.2) 0px 5px 10px, rgba(0, 0, 0, 0.4) 0px 15px 40px',
};
