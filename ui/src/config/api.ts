export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
  },
  NOTES: {
    LIST: '/notes/',
    CREATE: '/notes/',
    GET: (id: string) => `/notes/${id}`,
    UPDATE: (id: string) => `/notes/${id}`,
    DELETE: (id: string) => `/notes/${id}`,
  },
  SETTINGS: {
    USER_INFO: '/settings/user-info',
    CHANGE_PASSWORD: '/settings/change-password',
    EXPORT_NOTES: '/settings/export-notes',
    DELETE_ACCOUNT: '/settings/delete-account',
  },
} as const;
