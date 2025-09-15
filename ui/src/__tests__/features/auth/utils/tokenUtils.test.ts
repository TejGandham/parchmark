import {
  getTokenExpiration,
  isTokenExpiringSoon,
  getTokenExpirationWarningSeconds,
} from '../../../../features/auth/utils/tokenUtils';

// Mock the constants module
jest.mock('../../../../config/constants', () => ({
  TOKEN_WARNING_SECONDS: undefined, // Default to undefined
}));

// Import after mocking so we can manipulate it
import * as constants from '../../../../config/constants';

describe('tokenUtils', () => {
  describe('getTokenExpiration', () => {
    it('should decode valid JWT and return expiration time', () => {
      // Create a mock JWT with exp claim
      const exp = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      const result = getTokenExpiration(mockToken);
      expect(result).toBe(exp);
    });

    it('should return null for invalid JWT structure', () => {
      const invalidToken = 'invalid-token';
      const result = getTokenExpiration(invalidToken);
      expect(result).toBeNull();
    });

    it('should return null for JWT without exp claim', () => {
      const payload = { sub: 'user123' }; // No exp claim
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      const result = getTokenExpiration(mockToken);
      expect(result).toBeNull();
    });

    it('should handle base64url encoding (no padding)', () => {
      // Create payload that would normally need padding
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp, data: 'x' }; // Small payload
      // Remove padding from base64 to simulate base64url
      const encodedPayload = btoa(JSON.stringify(payload)).replace(/=/g, '');
      const mockToken = `header.${encodedPayload}.signature`;

      const result = getTokenExpiration(mockToken);
      expect(result).toBe(exp);
    });

    it('should handle JWT with special characters in base64url', () => {
      const exp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp };
      // Simulate base64url encoding (- and _ instead of + and /)
      const encodedPayload = btoa(JSON.stringify(payload))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
      const mockToken = `header.${encodedPayload}.signature`;

      const result = getTokenExpiration(mockToken);
      expect(result).toBe(exp);
    });

    it('should return null for null token', () => {
      const result = getTokenExpiration(null);
      expect(result).toBeNull();
    });

    it('should return null for malformed payload', () => {
      const mockToken = `header.not-valid-base64!@#$.signature`;

      // Mock console.error to verify it's called
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const result = getTokenExpiration(mockToken);
      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to decode JWT token:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });

  describe('getTokenExpirationWarningSeconds', () => {
    beforeEach(() => {
      // Reset mock to undefined before each test
      (constants as { TOKEN_WARNING_SECONDS?: string }).TOKEN_WARNING_SECONDS =
        undefined;
    });

    it('should return default 60 seconds when env variable is not set', () => {
      (constants as { TOKEN_WARNING_SECONDS?: string }).TOKEN_WARNING_SECONDS =
        undefined;
      expect(getTokenExpirationWarningSeconds()).toBe(60);
    });

    it('should return configured value from env variable', () => {
      (constants as { TOKEN_WARNING_SECONDS?: string }).TOKEN_WARNING_SECONDS =
        '120';
      expect(getTokenExpirationWarningSeconds()).toBe(120);
    });

    it('should return default for invalid env variable', () => {
      (constants as { TOKEN_WARNING_SECONDS?: string }).TOKEN_WARNING_SECONDS =
        'invalid';
      expect(getTokenExpirationWarningSeconds()).toBe(60);
    });
  });

  describe('isTokenExpiringSoon', () => {
    it('should return false for null token', () => {
      expect(isTokenExpiringSoon(null)).toBe(false);
    });

    it('should return false for token without expiration', () => {
      const payload = { sub: 'user123' }; // No exp claim
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      expect(isTokenExpiringSoon(mockToken)).toBe(false);
    });

    it('should return false for token expiring later than threshold', () => {
      // Token expires in 2 hours
      const exp = Math.floor(Date.now() / 1000) + 7200;
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      expect(isTokenExpiringSoon(mockToken)).toBe(false);
    });

    it('should return true for token expiring within default threshold', () => {
      // Token expires in 30 seconds
      const exp = Math.floor(Date.now() / 1000) + 30;
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      // Should return true since 30 < 60 (default) + 10 (clock skew)
      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });

    it('should respect custom threshold parameter', () => {
      // Token expires in 2 minutes
      const exp = Math.floor(Date.now() / 1000) + 120;
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      // Should return false with 30 second threshold
      expect(isTokenExpiringSoon(mockToken, 30)).toBe(false);

      // Should return true with 3 minute threshold
      expect(isTokenExpiringSoon(mockToken, 180)).toBe(true);
    });

    it('should account for clock skew buffer', () => {
      // Token expires exactly at threshold + clock skew
      const exp = Math.floor(Date.now() / 1000) + 70; // 60 (default) + 10 (clock skew)
      const payload = { exp };
      const encodedPayload = btoa(JSON.stringify(payload));
      const mockToken = `header.${encodedPayload}.signature`;

      // Should return true since exp <= now + 60 + 10 (clock skew)
      expect(isTokenExpiringSoon(mockToken)).toBe(true);
    });
  });
});
