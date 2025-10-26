// Comprehensive color palette for ParchMark
// Preserves existing primary colors and expands the design system

export const colors = {
  // Primary (Burgundy) - Existing colors preserved
  primary: {
    50: '#F2E8EB',
    100: '#E5D2D8',
    200: '#D8BBC4',
    300: '#BF94A1',
    400: '#A66C7E',
    500: '#8D455B',
    600: '#742E45',
    700: '#5B172E',
    800: '#580c24', // Main brand color
    900: '#42061A',
  },

  // Secondary (Complementary Green)
  secondary: {
    50: '#E8F5ED',
    100: '#C3E6D1',
    200: '#9DD7B5',
    300: '#76C899',
    400: '#4FB97D',
    500: '#2a7d40', // Complementary to primary
    600: '#246B37',
    700: '#1D592E',
    800: '#174724',
    900: '#11351B',
  },

  // Neutral (Warm Grays) - For text and UI elements
  neutral: {
    50: '#FAF9F7',
    100: '#F5F3F0',
    200: '#E9E6E1',
    300: '#D1CCC4',
    400: '#A8A199',
    500: '#7F7770',
    600: '#5F5851',
    700: '#403C37',
    800: '#2B2825',
    900: '#1A1816',
  },

  // Accent Colors for specific use cases
  accent: {
    blue: {
      50: '#EBF5FF',
      500: '#3B82F6',
      700: '#1D4ED8',
    },
    amber: {
      50: '#FFFBEB',
      500: '#F59E0B',
      700: '#B45309',
    },
    rose: {
      50: '#FFF1F2',
      500: '#F43F5E',
      700: '#BE123C',
    },
    emerald: {
      50: '#ECFDF5',
      500: '#10B981',
      700: '#047857',
    },
  },

  // Semantic Colors for feedback and status
  success: {
    50: '#ECFDF5',
    500: '#10B981',
    700: '#047857',
  },
  warning: {
    50: '#FFFBEB',
    500: '#F59E0B',
    700: '#B45309',
  },
  error: {
    50: '#FEF2F2',
    500: '#EF4444',
    700: '#B91C1C',
  },
  info: {
    50: '#EFF6FF',
    500: '#3B82F6',
    700: '#1D4ED8',
  },

  // Background & UI colors
  background: {
    light: '#FAF9F7',
    dark: '#1A1816',
    card: '#FFFFFF',
  },

  ui: {
    sidebar: '#FFFFFF',
    border: 'rgba(88, 12, 36, 0.1)',
    borderLight: 'rgba(88, 12, 36, 0.05)',
    divider: '#E9E6E1',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },
};
