export const STORAGE_KEYS = {
  AUTH: 'parchmark-auth',
  UI_PREFERENCES: 'parchmark-ui',
  THEME: 'parchmark-theme',
} as const;

export type StorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS];
