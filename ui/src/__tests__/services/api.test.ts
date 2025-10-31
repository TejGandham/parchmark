import '@testing-library/jest-dom/vitest';
import api, {
  login,
  refreshToken,
  getNotes,
  createNote,
  updateNote,
  deleteNote,
} from '../../services/api';
import { useAuthStore } from '../../features/auth/store';

// Mock fetch
global.fetch = vi.fn();
const mockFetch = fetch as MockedFunction<typeof fetch>;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock auth store
vi.mock('../../features/auth/store', () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ token: null })),
  },
}));

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.getItem.mockReturnValue(null); // Default to no token
    // Reset auth store mock to return no token by default
    (useAuthStore.getState as Mock).mockReturnValue({ token: null });
  });

  describe('getAuthToken', () => {
    it('should return null when no auth state in localStorage', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
        status: 200,
      } as Response);

      await getNotes();

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/', {
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should return null when auth state is invalid JSON', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
        status: 200,
      } as Response);

      await getNotes();

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/', {
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should return null when auth state has no token', async () => {
      localStorageMock.getItem.mockReturnValue(
        JSON.stringify({
          state: { user: 'test' },
        })
      );

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
        status: 200,
      } as Response);

      await getNotes();

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/', {
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should return token when auth state is valid', async () => {
      const token = 'test-token-123';
      // Mock the Zustand store to return the token
      (useAuthStore.getState as Mock).mockReturnValue({ token });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
        status: 200,
      } as Response);

      await getNotes();

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/', {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
    });
  });

  describe('request function', () => {
    it('should handle successful responses', async () => {
      const mockData = [{ id: '1', title: 'Test' }];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        status: 200,
      } as Response);

      const result = await getNotes();
      expect(result).toEqual(mockData);
    });

    it('should handle 204 responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response);

      const result = await deleteNote('1');
      expect(result).toBeNull();
    });

    it('should handle error responses with string detail', async () => {
      const errorMessage = 'Not found';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: errorMessage }),
      } as Response);

      await expect(getNotes()).rejects.toThrow(errorMessage);
    });

    it('should handle error responses with array detail', async () => {
      const errorMessage = 'Validation error';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ detail: [{ msg: errorMessage }] }),
      } as Response);

      await expect(getNotes()).rejects.toThrow(errorMessage);
    });

    it('should handle error responses without detail', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}),
      } as Response);

      await expect(getNotes()).rejects.toThrow('HTTP error! status: 500');
    });

    it('should handle error responses with malformed JSON', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      } as Response);

      await expect(getNotes()).rejects.toThrow('HTTP error! status: 500');
    });
  });

  describe('login', () => {
    it('should make POST request to login endpoint', async () => {
      const loginResponse = {
        access_token: 'token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => loginResponse,
        status: 200,
      } as Response);

      const result = await login('testuser', 'password123');

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: 'testuser', password: 'password123' }),
      });
      expect(result).toEqual(loginResponse);
    });
  });

  describe('refreshToken', () => {
    it('should make POST request to refresh endpoint', async () => {
      const refreshResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => refreshResponse,
        status: 200,
      } as Response);

      const result = await refreshToken('old-refresh-token');

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: 'old-refresh-token' }),
      });
      expect(result).toEqual(refreshResponse);
    });
  });

  describe('getNotes', () => {
    it('should make GET request to notes endpoint', async () => {
      const notes = [{ id: '1', title: 'Test Note', content: 'Content' }];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => notes,
        status: 200,
      } as Response);

      const result = await getNotes();

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/', {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      expect(result).toEqual(notes);
    });
  });

  describe('createNote', () => {
    it('should make POST request to notes endpoint', async () => {
      const noteData = { title: 'New Note', content: 'New content' };
      const createdNote = {
        id: '2',
        ...noteData,
        createdAt: '2023-01-01',
        updatedAt: '2023-01-01',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => createdNote,
        status: 201,
      } as Response);

      const result = await createNote(noteData);

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(noteData),
      });
      expect(result).toEqual(createdNote);
    });
  });

  describe('updateNote', () => {
    it('should make PUT request to specific note endpoint', async () => {
      const noteUpdate = { content: 'Updated content' };
      const updatedNote = {
        id: '1',
        title: 'Test',
        content: 'Updated content',
        createdAt: '2023-01-01',
        updatedAt: '2023-01-02',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedNote,
        status: 200,
      } as Response);

      const result = await updateNote('1', noteUpdate);

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(noteUpdate),
      });
      expect(result).toEqual(updatedNote);
    });
  });

  describe('deleteNote', () => {
    it('should make DELETE request to specific note endpoint', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response);

      const result = await deleteNote('1');

      expect(mockFetch).toHaveBeenCalledWith('/api/notes/1', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      expect(result).toBeNull();
    });
  });

  describe('default export', () => {
    it('should export all API functions', () => {
      expect(api.login).toBe(login);
      expect(api.refreshToken).toBe(refreshToken);
      expect(api.getNotes).toBe(getNotes);
      expect(api.createNote).toBe(createNote);
      expect(api.updateNote).toBe(updateNote);
      expect(api.deleteNote).toBe(deleteNote);
    });
  });

  describe('ApiError', () => {
    it('should create proper error instances', async () => {
      const errorData = { detail: 'Custom error' };
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorData,
      } as Response);

      try {
        await getNotes();
      } catch (error: unknown) {
        expect(error).toBeInstanceOf(Error);
        const apiError = error as Error & { status?: number; data?: unknown };
        expect(apiError.message).toBe('Custom error');
        expect(apiError.status).toBe(400);
        expect(apiError.data).toEqual(errorData);
        expect(apiError.name).toBe('Error');
      }
    });
  });

  describe('401 error handling', () => {
    it('should attempt token refresh on 401 error for non-login endpoints', async () => {
      const mockLogout = vi.fn();
      const mockRefreshTokens = vi.fn().mockResolvedValue(false); // Refresh fails
      (useAuthStore.getState as Mock).mockReturnValue({
        token: 'some-token',
        actions: { logout: mockLogout, refreshTokens: mockRefreshTokens },
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      } as Response);

      await expect(getNotes()).rejects.toThrow('Unauthorized');
      expect(mockRefreshTokens).toHaveBeenCalled();
      expect(mockLogout).toHaveBeenCalled();
    });

    it('should retry request after successful token refresh on 401 error', async () => {
      const mockLogout = vi.fn();
      const mockRefreshTokens = vi.fn().mockResolvedValue(true); // Refresh succeeds
      (useAuthStore.getState as Mock).mockReturnValue({
        token: 'some-token',
        actions: { logout: mockLogout, refreshTokens: mockRefreshTokens },
      });

      const notes = [{ id: '1', title: 'Test Note', content: 'Content' }];

      // First request returns 401
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      } as Response);

      // Second request (retry) succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => notes,
        status: 200,
      } as Response);

      const result = await getNotes();

      expect(mockRefreshTokens).toHaveBeenCalled();
      expect(mockLogout).not.toHaveBeenCalled();
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(notes);
    });

    it('should NOT call logout on 401 error for login endpoint', async () => {
      const mockLogout = vi.fn();
      const mockRefreshTokens = vi.fn();
      (useAuthStore.getState as Mock).mockReturnValue({
        token: null,
        actions: { logout: mockLogout, refreshTokens: mockRefreshTokens },
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      } as Response);

      await expect(login('user', 'wrong')).rejects.toThrow(
        'Invalid credentials'
      );
      expect(mockLogout).not.toHaveBeenCalled();
      expect(mockRefreshTokens).not.toHaveBeenCalled();
    });
  });
});
