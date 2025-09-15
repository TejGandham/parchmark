import { Note } from '../types';
import { API_BASE_URL } from '../config/constants';

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
  const authState = localStorage.getItem('parchmark-auth');
  if (!authState) return null;
  try {
    const { state } = JSON.parse(authState);
    return state.token || null;
  } catch (error) {
    return null;
  }
};

const request = async <T>(
  endpoint: string,
  options: RequestInit = {}
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
    
    // Handle 401 errors by logging out (except for login endpoint)
    if (response.status === 401 && !endpoint.includes('/auth/login')) {
      // Dynamically import to avoid circular dependency
      const { useAuthStore } = await import('../features/auth/store');
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
): Promise<{ access_token: string; token_type: string }> => {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
};

// Notes API
export const getNotes = (): Promise<Note[]> => request('/notes/');

export const createNote = (note: {
  title: string;
  content: string;
}): Promise<Note> =>
  request('/notes/', {
    method: 'POST',
    body: JSON.stringify(note),
  });

export const updateNote = (
  id: string,
  note: { content: string }
): Promise<Note> =>
  request(`/notes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(note),
  });

export const deleteNote = (id: string): Promise<void> =>
  request(`/notes/${id}`, {
    method: 'DELETE',
  });

export default {
  login,
  getNotes,
  createNote,
  updateNote,
  deleteNote,
};
