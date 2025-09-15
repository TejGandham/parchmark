import { getTokenExpiration, isTokenExpiringSoon } from '../../../../features/auth/utils/tokenUtils';

describe('Token Utilities', () => {
  describe('getTokenExpiration', () => {
    it('should extract expiration from valid JWT token', () => {
      // Create a mock JWT with exp claim set to a future timestamp
      const exp = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const payload = { exp, sub: 'user123' };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      const result = getTokenExpiration(mockToken);
      expect(result).toBe(exp);
    });

    it('should handle base64url encoding with special characters', () => {
      // Create payload with base64url encoding (- and _ instead of + and /)
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp };
      const base64 = btoa(JSON.stringify(payload));
      // Convert to base64url format
      const base64url = base64.replace(/\+/g, '-').replace(/\//g, '_');
      const mockToken = `header.${base64url}.signature`;
      
      const result = getTokenExpiration(mockToken);
      expect(result).toBe(exp);
    });

    it('should return null for token without exp claim', () => {
      const payload = { sub: 'user123' }; // No exp claim
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      const result = getTokenExpiration(mockToken);
      expect(result).toBeNull();
    });

    it('should return null for invalid token format', () => {
      expect(getTokenExpiration('invalid-token')).toBeNull();
      expect(getTokenExpiration('')).toBeNull();
      expect(getTokenExpiration('only.two')).toBeNull();
    });

    it('should return null for malformed payload', () => {
      const mockToken = 'header.invalid-base64!@#.signature';
      const result = getTokenExpiration(mockToken);
      expect(result).toBeNull();
    });
  });

  describe('isTokenExpiringSoon', () => {
    it('should return true if token is null', () => {
      expect(isTokenExpiringSoon(null)).toBe(true);
    });

    it('should return true if token is already expired', () => {
      const exp = Math.floor(Date.now() / 1000) - 100; // 100 seconds ago
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });

    it('should return true if token expires within default 60 seconds', () => {
      const exp = Math.floor(Date.now() / 1000) + 30; // 30 seconds from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });

    it('should return false if token expires after default 60 seconds', () => {
      const exp = Math.floor(Date.now() / 1000) + 120; // 2 minutes from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      expect(isTokenExpiringSoon(mockToken)).toBe(false);
    });

    it('should respect custom withinSeconds parameter', () => {
      const exp = Math.floor(Date.now() / 1000) + 150; // 2.5 minutes from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      // Should return true when checking within 180 seconds (3 minutes)
      expect(isTokenExpiringSoon(mockToken, 180)).toBe(true);
      
      // Should return false when checking within 120 seconds (2 minutes)
      expect(isTokenExpiringSoon(mockToken, 120)).toBe(false);
    });

    it('should return true for invalid token format', () => {
      expect(isTokenExpiringSoon('invalid-token')).toBe(true);
    });

    it('should handle edge case of exact expiration time', () => {
      const exp = Math.floor(Date.now() / 1000) + 60; // Exactly 60 seconds from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;
      
      // Should return true since exp <= now + 60
      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });
  });
});