import { describe, it, expect } from 'vitest';
import { API_ENDPOINTS } from '../../config/api';

describe('API_ENDPOINTS', () => {
  describe('AUTH endpoints', () => {
    it('should have LOGIN endpoint', () => {
      expect(API_ENDPOINTS.AUTH.LOGIN).toBe('/auth/login');
    });

    it('should have LOGOUT endpoint', () => {
      expect(API_ENDPOINTS.AUTH.LOGOUT).toBe('/auth/logout');
    });

    it('should have REFRESH endpoint', () => {
      expect(API_ENDPOINTS.AUTH.REFRESH).toBe('/auth/refresh');
    });

    it('should have ME endpoint', () => {
      expect(API_ENDPOINTS.AUTH.ME).toBe('/auth/me');
    });
  });

  describe('NOTES endpoints', () => {
    it('should have LIST endpoint', () => {
      expect(API_ENDPOINTS.NOTES.LIST).toBe('/notes/');
    });

    it('should have CREATE endpoint', () => {
      expect(API_ENDPOINTS.NOTES.CREATE).toBe('/notes/');
    });

    it('should generate correct GET endpoint with id', () => {
      expect(API_ENDPOINTS.NOTES.GET('note-123')).toBe('/notes/note-123');
      expect(API_ENDPOINTS.NOTES.GET('note-456')).toBe('/notes/note-456');
    });

    it('should generate correct UPDATE endpoint with id', () => {
      expect(API_ENDPOINTS.NOTES.UPDATE('note-123')).toBe('/notes/note-123');
      expect(API_ENDPOINTS.NOTES.UPDATE('note-789')).toBe('/notes/note-789');
    });

    it('should generate correct DELETE endpoint with id', () => {
      expect(API_ENDPOINTS.NOTES.DELETE('note-123')).toBe('/notes/note-123');
      expect(API_ENDPOINTS.NOTES.DELETE('note-abc')).toBe('/notes/note-abc');
    });
  });
});
