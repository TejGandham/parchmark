import { extendTheme } from '@chakra-ui/react';
import tokens from './tokens';

const theme = extendTheme({
  colors: {
    brand: tokens.colors.primary,
  },
  config: {
    initialColorMode: 'light',
    useSystemColorMode: false,
  },
  fonts: tokens.fonts,
  shadows: tokens.shadows,
  radii: tokens.radii,
  space: tokens.spacing,
  transition: tokens.transitions,
});

export default theme;