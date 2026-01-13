import { Note } from '../types';
import { API_BASE_URL } from '../config/constants';
import { useAuthStore } from '../features/auth/store';
import { API_ENDPOINTS } from '../config/api';

type ApiErrorResponse = {
  detail?: string | { msg: string }[];
};

class ApiError extends Error {
  status: number;
  data: ApiErrorResponse;

  constructor(message: string, status: number, data: ApiErrorResponse) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

const getAuthToken = (): string | null => {
  // Use Zustand store directly instead of parsing localStorage
  return useAuthStore.getState().token;
};

const request = async <T>(
  endpoint: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData: ApiErrorResponse = await response.json().catch(() => ({}));

    // Handle 401 errors with token refresh retry
    if (
      response.status === 401 &&
      !endpoint.includes(API_ENDPOINTS.AUTH.LOGIN) &&
      !endpoint.includes(API_ENDPOINTS.AUTH.REFRESH) &&
      !isRetry
    ) {
      // Try to refresh the token
      const refreshSuccess = await useAuthStore
        .getState()
        .actions.refreshTokens();

      if (refreshSuccess) {
        // Retry the original request with the new token
        return request<T>(endpoint, options, true);
      } else {
        // Refresh failed, logout
        useAuthStore.getState().actions.logout();
      }
    }

    // If this is a 401 on refresh endpoint or a retry, just logout
    if (
      response.status === 401 &&
      (endpoint.includes(API_ENDPOINTS.AUTH.REFRESH) || isRetry)
    ) {
      useAuthStore.getState().actions.logout();
    }

    let errorMessage = `HTTP error! status: ${response.status}`;
    if (errorData.detail) {
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail) && errorData.detail[0]?.msg) {
        errorMessage = errorData.detail[0].msg;
      }
    }
    throw new ApiError(errorMessage, response.status, errorData);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
};

// Auth API
export const login = (
  username: string,
  password: string
): Promise<{
  access_token: string;
  refresh_token: string;
  token_type: string;
}> => {
  return request(API_ENDPOINTS.AUTH.LOGIN, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
};

export const refreshToken = (
  refreshToken: string
): Promise<{
  access_token: string;
  refresh_token: string;
  token_type: string;
}> => {
  return request(API_ENDPOINTS.AUTH.REFRESH, {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
};

// Notes API
export const getNotes = (): Promise<Note[]> =>
  request(API_ENDPOINTS.NOTES.LIST);

export const createNote = (note: {
  title: string;
  content: string;
}): Promise<Note> =>
  request(API_ENDPOINTS.NOTES.CREATE, {
    method: 'POST',
    body: JSON.stringify(note),
  });

export const updateNote = (
  id: string,
  note: { content: string }
): Promise<Note> =>
  request(API_ENDPOINTS.NOTES.UPDATE(id), {
    method: 'PUT',
    body: JSON.stringify(note),
  });

export const deleteNote = (id: string): Promise<void> =>
  request(API_ENDPOINTS.NOTES.DELETE(id), {
    method: 'DELETE',
  });

// Settings API
export interface UserInfo {
  username: string;
  email: string | null;
  created_at: string;
  notes_count: number;
  auth_provider: 'local' | 'oidc';
}

export const getUserInfo = (): Promise<UserInfo> =>
  request(API_ENDPOINTS.SETTINGS.USER_INFO);

export const changePassword = (
  currentPassword: string,
  newPassword: string
): Promise<{ message: string }> =>
  request(API_ENDPOINTS.SETTINGS.CHANGE_PASSWORD, {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

export const exportNotes = async (): Promise<Blob> => {
  const token = getAuthToken();
  const headers: HeadersInit = {};

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}${API_ENDPOINTS.SETTINGS.EXPORT_NOTES}`,
    { headers }
  );

  if (!response.ok) {
    throw new ApiError(
      'Failed to export notes',
      response.status,
      await response.json().catch(() => ({}))
    );
  }

  return response.blob();
};

export const deleteAccount = (password: string): Promise<{ message: string }> =>
  request(API_ENDPOINTS.SETTINGS.DELETE_ACCOUNT, {
    method: 'DELETE',
    body: JSON.stringify({ password }),
  });

export default {
  login,
  refreshToken,
  getNotes,
  createNote,
  updateNote,
  deleteNote,
  getUserInfo,
  changePassword,
  exportNotes,
  deleteAccount,
};
