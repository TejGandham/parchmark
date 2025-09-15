import {
  getTokenExpiration,
  isTokenExpiringSoon,
  getTokenExpirationWarningSeconds,
} from '../../../../features/auth/utils/tokenUtils';

describe('Token Utilities', () => {
  describe('getTokenExpirationWarningSeconds', () => {
    it('should return default value when environment variable is not set', () => {
      // Mock import.meta.env without VITE_TOKEN_WARNING_SECONDS
      const originalEnv = import.meta.env;
      import.meta.env = { ...originalEnv };
      delete import.meta.env.VITE_TOKEN_WARNING_SECONDS;

      expect(getTokenExpirationWarningSeconds()).toBe(60);

      import.meta.env = originalEnv;
    });

    it('should return parsed value from environment variable', () => {
      // Mock import.meta.env with VITE_TOKEN_WARNING_SECONDS
      const originalEnv = import.meta.env;
      import.meta.env = { ...originalEnv, VITE_TOKEN_WARNING_SECONDS: '120' };

      expect(getTokenExpirationWarningSeconds()).toBe(120);

      import.meta.env = originalEnv;
    });
  });

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

    it('should return null for malformed payload and log error', () => {
      // Mock console.error to verify it's called
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      const mockToken = 'header.invalid-base64!@#.signature';
      const result = getTokenExpiration(mockToken);
      expect(result).toBeNull();

      // Verify error was logged
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to decode JWT token:',
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
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

    it('should return true if token expires within default 60 seconds plus clock skew buffer', () => {
      // With 10 second clock skew buffer, tokens expiring within 70 seconds should return true
      const exp = Math.floor(Date.now() / 1000) + 65; // 65 seconds from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });

    it('should return false if token expires after default 60 seconds plus clock skew buffer', () => {
      // With 10 second clock skew buffer, tokens expiring after 70 seconds should return false
      const exp = Math.floor(Date.now() / 1000) + 80; // 80 seconds from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      expect(isTokenExpiringSoon(mockToken)).toBe(false);
    });

    it('should respect custom withinSeconds parameter with clock skew', () => {
      const exp = Math.floor(Date.now() / 1000) + 150; // 2.5 minutes from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      // With 10 second clock skew, should return true when checking within 140 seconds (150 - 10)
      expect(isTokenExpiringSoon(mockToken, 140)).toBe(true);

      // Should return false when checking within 130 seconds (less than 150 - 10)
      expect(isTokenExpiringSoon(mockToken, 130)).toBe(false);
    });

    it('should return true for invalid token format', () => {
      expect(isTokenExpiringSoon('invalid-token')).toBe(true);
    });

    it('should handle edge case of exact expiration time with clock skew', () => {
      const exp = Math.floor(Date.now() / 1000) + 70; // Exactly 70 seconds from now (60 + 10 clock skew)
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      // Should return true since exp <= now + 60 + 10 (clock skew)
      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });
  });
});