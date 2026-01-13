// Input component theme with custom variants
// Usage: <Input variant="elevated" /> or <Input variant="filled" />

import { inputAnatomy } from '@chakra-ui/anatomy';
import { createMultiStyleConfigHelpers } from '@chakra-ui/react';

const { definePartsStyle, defineMultiStyleConfig } =
  createMultiStyleConfigHelpers(inputAnatomy.keys);

// Base style for all inputs
const baseStyle = definePartsStyle({
  field: {
    borderRadius: 'md',
    borderWidth: '2px',
    borderColor: 'border.default',
    bg: 'bg.surface',
    transition: 'all 0.2s',
    _focus: {
      borderColor: 'primary.800',
      boxShadow: 'outline',
    },
    _hover: {
      borderColor: 'neutral.300',
    },
    _invalid: {
      borderColor: 'error.500',
      boxShadow: '0 0 0 1px var(--chakra-colors-error-500)',
    },
  },
});

// Elevated variant - adds shadow on focus
const variantElevated = definePartsStyle({
  field: {
    boxShadow: 'sm',
    _focus: {
      boxShadow: 'outline, sm',
    },
  },
});

// Filled variant - background fill style
const variantFilled = definePartsStyle({
  field: {
    bg: 'bg.subtle',
    borderColor: 'transparent',
    _hover: {
      bg: 'interactive.hover',
    },
    _focus: {
      bg: 'bg.surface',
      borderColor: 'primary.800',
    },
  },
});

export const Input = defineMultiStyleConfig({
  baseStyle,
  variants: {
    elevated: variantElevated,
    filled: variantFilled,
  },
  defaultProps: {
    size: 'md',
  },
});
