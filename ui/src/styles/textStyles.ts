// Typography presets for consistent text styling
// Apply with textStyle prop: <Text textStyle="h1" />

export const textStyles = {
  // Display text - Hero/large headings
  display: {
    fontSize: ['4xl', '5xl', '6xl'],
    fontWeight: 'bold',
    fontFamily: 'heading',
    letterSpacing: 'tight',
    lineHeight: 'tight',
  },

  // Page headings - Responsive sizes
  h1: {
    fontSize: ['3xl', '4xl', '5xl'],
    fontWeight: 'bold',
    fontFamily: 'heading',
    letterSpacing: 'tight',
    lineHeight: 'tight',
  },
  h2: {
    fontSize: ['2xl', '3xl', '4xl'],
    fontWeight: 'semibold',
    fontFamily: 'heading',
    letterSpacing: 'tight',
    lineHeight: 'snug',
  },
  h3: {
    fontSize: ['xl', '2xl', '3xl'],
    fontWeight: 'semibold',
    fontFamily: 'heading',
    letterSpacing: 'tight',
    lineHeight: 'snug',
  },

  // Body text variations
  body: {
    fontSize: 'md',
    fontWeight: 'normal',
    lineHeight: 'relaxed',
    color: 'text.primary',
  },
  bodyLarge: {
    fontSize: 'lg',
    fontWeight: 'normal',
    lineHeight: 'relaxed',
    color: 'text.primary',
  },
  bodySmall: {
    fontSize: 'sm',
    fontWeight: 'normal',
    lineHeight: 'normal',
    color: 'text.secondary',
  },

  // Special text styles
  label: {
    fontSize: 'sm',
    fontWeight: 'medium',
    textTransform: 'uppercase',
    letterSpacing: 'wider',
    color: 'text.secondary',
  },
  caption: {
    fontSize: 'xs',
    fontWeight: 'normal',
    color: 'text.muted',
    lineHeight: 'normal',
  },
  code: {
    fontFamily: 'mono',
    fontSize: 'sm',
    bg: 'bg.subtle',
    px: 1,
    py: 0.5,
    borderRadius: 'sm',
  },
};
