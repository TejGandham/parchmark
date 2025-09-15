// JWT token utility functions

interface JWTPayload {
  exp?: number;
  sub?: string;
  [key: string]: unknown;
}

/**
 * Decode a JWT token without verification (client-side only)
 * @param token - JWT token string
 * @returns Decoded payload or null if invalid
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    // Decode the payload (second part)
    const payload = parts[1];
    // Handle URL-safe base64
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    // Add padding if needed
    const padded = base64 + '=='.substring(0, (4 - base64.length % 4) % 4);
    
    const decoded = atob(padded);
    return JSON.parse(decoded) as JWTPayload;
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

/**
 * Get the expiration time from a JWT token
 * @param token - JWT token string
 * @returns Expiration timestamp in milliseconds or null
 */
export function getTokenExpiration(token: string): number | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return null;
  }
  // JWT exp is in seconds, convert to milliseconds
  return payload.exp * 1000;
}

/**
 * Check if a JWT token is expired or will expire soon
 * @param token - JWT token string
 * @param bufferSeconds - Number of seconds before actual expiration to consider it expired (default: 30)
 * @returns true if token is expired or will expire within buffer time
 */
export function isTokenExpired(token: string, bufferSeconds: number = 30): boolean {
  const expiration = getTokenExpiration(token);
  if (!expiration) {
    return true; // Consider invalid tokens as expired
  }
  
  const now = Date.now();
  const bufferMs = bufferSeconds * 1000;
  
  return now >= (expiration - bufferMs);
}

/**
 * Calculate time until token expires
 * @param token - JWT token string
 * @returns Time in milliseconds until expiration, or 0 if already expired
 */
export function getTimeUntilExpiration(token: string): number {
  const expiration = getTokenExpiration(token);
  if (!expiration) {
    return 0;
  }
  
  const now = Date.now();
  const timeLeft = expiration - now;
  
  return Math.max(0, timeLeft);
}