/**
 * JWT payload interface with standard claims
 */
export interface JWTPayload {
  exp?: number;
  sub?: string;
  iat?: number;
  nbf?: number;
  iss?: string;
  aud?: string | string[];
  [key: string]: unknown;
}

/**
 * Clock skew buffer in seconds to account for server/client time differences
 */
const CLOCK_SKEW_BUFFER_SECONDS = 10;

/**
 * Simple JWT token expiration check
 * @param token - JWT token string
 * @returns Expiration timestamp in seconds or null if invalid
 */
export function getTokenExpiration(token: string): number | null {
  try {
    // Simple JWT decoding - extract payload
    const base64Url = token.split('.')[1];
    if (!base64Url) return null;
    
    // Convert base64url to base64
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    // Decode and parse
    const payload: JWTPayload = JSON.parse(atob(base64));
    
    return payload.exp || null;
  } catch (error) {
    // Log error for debugging malformed tokens
    console.error('Failed to decode JWT token:', error);
    return null;
  }
}

/**
 * Get token expiration warning threshold from environment or use default
 * @returns Warning threshold in seconds
 */
export function getTokenExpirationWarningSeconds(): number {
  const envValue = import.meta.env.VITE_TOKEN_WARNING_SECONDS;
  return envValue ? parseInt(envValue, 10) : 60;
}

/**
 * Check if token expires within the given seconds
 * @param token - JWT token string  
 * @param withinSeconds - Check if expires within this many seconds (uses env var or default: 60)
 * @returns true if token is expired or expires soon
 */
export function isTokenExpiringSoon(token: string | null, withinSeconds?: number): boolean {
  if (!token) return true;
  
  const exp = getTokenExpiration(token);
  if (!exp) return true;
  
  // Use provided value, environment variable, or default
  const threshold = withinSeconds ?? getTokenExpirationWarningSeconds();
  
  // Add clock skew buffer to account for time differences
  const now = Math.floor(Date.now() / 1000);
  return exp <= now + threshold + CLOCK_SKEW_BUFFER_SECONDS;
}