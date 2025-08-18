import '@testing-library/jest-dom';
import api, {
  login,
  getNotes,
  createNote,
  updateNote,
  deleteNote,
} from '../../services/api';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.getItem.mockReturnValue(null); // Default to no token
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
      localStorageMock.getItem.mockReturnValue(
        JSON.stringify({
          state: { token },
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
      const loginResponse = { access_token: 'token', token_type: 'bearer' };
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
      } catch (error: any) {
        expect(error.message).toBe('Custom error');
        expect(error.status).toBe(400);
        expect(error.data).toEqual(errorData);
        expect(error.name).toBe('Error');
      }
    });
  });
});
