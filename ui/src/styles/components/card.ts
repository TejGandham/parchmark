// Card component theme with custom variants
// Usage: <Card variant="elevated"><CardBody>Content</CardBody></Card>

import { cardAnatomy } from '@chakra-ui/anatomy';
import { createMultiStyleConfigHelpers } from '@chakra-ui/react';

const { definePartsStyle, defineMultiStyleConfig } =
  createMultiStyleConfigHelpers(cardAnatomy.keys);

// Base style for all cards
const baseStyle = definePartsStyle({
  container: {
    bg: 'bg.surface',
    borderRadius: 'lg',
    overflow: 'hidden',
  },
  header: {
    px: 6,
    py: 4,
  },
  body: {
    px: 6,
    py: 4,
  },
  footer: {
    px: 6,
    py: 4,
  },
});

// Elevated variant - shadow with border
const variantElevated = definePartsStyle({
  container: {
    boxShadow: 'card',
    border: '1px',
    borderColor: 'border.default',
    transition: 'all 0.2s',
  },
});

// Outlined variant - border only, no shadow
const variantOutlined = definePartsStyle({
  container: {
    border: '1px',
    borderColor: 'border.default',
  },
});

// Interactive variant - hover effects for clickable cards
const variantInteractive = definePartsStyle({
  container: {
    boxShadow: 'card',
    border: '1px',
    borderColor: 'transparent',
    cursor: 'pointer',
    transition: 'all 0.15s',
    _hover: {
      borderColor: 'border.emphasis',
      boxShadow: 'cardHover',
      transform: 'translateY(-2px)',
    },
    _active: {
      transform: 'translateY(0)',
    },
  },
});

export const Card = defineMultiStyleConfig({
  baseStyle,
  variants: {
    elevated: variantElevated,
    outlined: variantOutlined,
    interactive: variantInteractive,
  },
  defaultProps: {
    variant: 'elevated',
  },
});
