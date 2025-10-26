// Main theme configuration for ParchMark
// Integrates all foundations, components, and styles

import { extendTheme, withDefaultColorScheme } from '@chakra-ui/react';
import {
  colors,
  typography,
  shadows,
  spacing,
  radii,
  semanticTokens,
} from './foundations';
import { layerStyles } from './layerStyles';
import { textStyles } from './textStyles';
import { Button, Input, Card } from './components';
import { globalStyles } from './global';

const theme = extendTheme(
  {
    config: {
      initialColorMode: 'light',
      useSystemColorMode: false,
    },

    // Foundations
    colors,
    ...typography,
    shadows,
    space: spacing,
    radii,
    semanticTokens,

    // Styles
    layerStyles,
    textStyles,
    styles: globalStyles,

    // Components
    components: {
      Button,
      Input,
      Card,
    },
  },

  // Apply primary color scheme to all components by default
  withDefaultColorScheme({ colorScheme: 'primary' })
);

export default theme;
