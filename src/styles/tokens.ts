// Design tokens for consistent application styling

export const colors = {
  primary: {
    main: '#580c24', // Deep burgundy
    light: '#8a3b53', // Lighter burgundy
    dark: '#42061A', // Darker burgundy
    50: '#F2E8EB',
    100: '#E5D2D8',
    200: '#D8BBC4',
    300: '#BF94A1',
    400: '#A66C7E',
    500: '#8D455B',
    600: '#742E45',
    700: '#5B172E',
    800: '#580c24',
    900: '#42061A',
  },
  complementary: '#2a7d40', // Complementary green
  background: {
    light: 'gray.50',
    dark: 'gray.900',
  },
  ui: {
    sidebar: 'white',
    border: 'rgba(88, 12, 36, 0.1)',
  },
};

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  xxl: '3rem',
};

export const fonts = {
  heading: "'Playfair Display', serif",
  body: "'Inter', sans-serif",
  mono: "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace",
};

export const transitions = {
  default: 'all 0.3s ease-in-out',
  fast: 'all 0.15s ease-in-out',
  slow: 'all 0.5s ease-in-out',
};

export const shadows = {
  sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
  sidebar: '3px 0 10px rgba(0, 0, 0, 0.05)',
  sidebarDark: '3px 0 15px rgba(0, 0, 0, 0.25)',
};

export const radii = {
  sm: '0.125rem',
  md: '0.25rem',
  lg: '0.5rem',
  xl: '1rem',
  full: '9999px',
};

export default {
  colors,
  spacing,
  fonts,
  transitions,
  shadows,
  radii,
};
