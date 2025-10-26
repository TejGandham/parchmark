// Reusable layer styles for common component patterns
// Apply with layerStyle prop: <Box layerStyle="card" />

export const layerStyles = {
  // Basic card - White background with shadow
  card: {
    bg: 'bg.surface',
    borderRadius: 'lg',
    border: '1px',
    borderColor: 'border.default',
    boxShadow: 'card',
    transition: 'all 0.2s',
    _hover: {
      boxShadow: 'cardHover',
    },
  },

  // Interactive card - For clickable cards (note items, etc.)
  cardInteractive: {
    bg: 'bg.surface',
    borderRadius: 'lg',
    border: '1px',
    borderColor: 'transparent',
    boxShadow: 'card',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    position: 'relative',
    _hover: {
      bg: 'interactive.hover',
      borderColor: 'border.emphasis',
      transform: 'translateX(2px)',
    },
    _active: {
      bg: 'interactive.active',
      borderColor: 'primary.500',
    },
  },

  // Selected card - For active/selected state (active note)
  cardSelected: {
    bg: 'interactive.active',
    borderRadius: 'lg',
    border: '1px',
    borderColor: 'primary.500',
    boxShadow: 'card',
    position: 'relative',
    _before: {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: '4px',
      bgGradient: 'linear(to-b, primary.800, primary.600)',
      borderRadius: 'lg 0 0 lg',
    },
  },

  // Glass effect - For overlays and special surfaces
  glass: {
    bg: 'rgba(255, 255, 255, 0.8)',
    backdropFilter: 'blur(10px)',
    borderRadius: 'xl',
    border: '1px',
    borderColor: 'whiteAlpha.400',
    _dark: {
      bg: 'rgba(26, 24, 22, 0.8)',
      borderColor: 'whiteAlpha.100',
    },
  },

  // Raised surface - For elevated elements
  raised: {
    bg: 'bg.surface',
    borderRadius: 'lg',
    boxShadow: 'lg',
    border: '1px',
    borderColor: 'border.default',
  },

  // Well/inset - For sunken surfaces
  well: {
    bg: 'bg.subtle',
    borderRadius: 'md',
    boxShadow: 'inner',
    border: '1px',
    borderColor: 'border.default',
  },
};
