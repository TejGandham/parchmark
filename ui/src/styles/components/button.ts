// Button component theme with custom variants
// Usage: <Button variant="primary" size="md">Save</Button>

import { defineStyleConfig } from '@chakra-ui/react';

export const Button = defineStyleConfig({
  // Base styles applied to all variants
  baseStyle: {
    fontWeight: 'semibold',
    borderRadius: 'md',
    transition: 'all 0.2s',
    _focus: {
      boxShadow: 'outline',
    },
  },

  // Size variations
  sizes: {
    sm: {
      fontSize: 'sm',
      px: 3,
      py: 2,
      h: 8,
    },
    md: {
      fontSize: 'md',
      px: 4,
      py: 2.5,
      h: 10,
    },
    lg: {
      fontSize: 'lg',
      px: 6,
      py: 3,
      h: 12,
    },
  },

  // Style variants
  variants: {
    // Primary gradient button with shadow and hover lift
    primary: {
      bgGradient: 'linear(to-r, primary.800, primary.600)',
      color: 'white',
      boxShadow: 'primarySm',
      _hover: {
        bgGradient: 'linear(to-r, primary.700, primary.500)',
        transform: 'translateY(-2px)',
        boxShadow: 'primary',
        _disabled: {
          transform: 'none',
        },
      },
      _active: {
        transform: 'translateY(0)',
        boxShadow: 'primarySm',
      },
    },

    // Secondary outline button
    secondary: {
      borderWidth: '2px',
      borderColor: 'primary.800',
      color: 'primary.800',
      bg: 'transparent',
      _hover: {
        bg: 'primary.50',
        transform: 'translateY(-1px)',
      },
      _active: {
        transform: 'translateY(0)',
        bg: 'primary.100',
      },
    },

    // Ghost button for subtle actions
    ghost: {
      bg: 'transparent',
      color: 'text.primary',
      _hover: {
        bg: 'interactive.hover',
      },
      _active: {
        bg: 'interactive.active',
      },
    },

    // Subtle button with light background
    subtle: {
      bg: 'bg.subtle',
      color: 'text.primary',
      _hover: {
        bg: 'interactive.hover',
      },
      _active: {
        bg: 'interactive.active',
      },
    },
  },

  // Default props
  defaultProps: {
    size: 'md',
    variant: 'primary',
  },
});
