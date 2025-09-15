// JWT Payload structure
interface JWTPayload {
  exp?: number; // Expiration time (NumericDate)
  sub?: string; // Subject
  iat?: number; // Issued at
  nbf?: number; // Not before
  iss?: string; // Issuer
  aud?: string | string[]; // Audience
  [key: string]: unknown; // Allow additional claims
}

// Clock skew buffer in seconds to account for time differences
const CLOCK_SKEW_BUFFER_SECONDS = 10;

/**
 * Decode a JWT token and extract the expiration timestamp
 * @param token JWT token string
 * @returns Expiration timestamp in seconds or null if not available
 */
export function getTokenExpiration(token: string | null): number | null {
  if (!token) return null;

  try {
    // Split token and get payload
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    // Decode base64url payload
    let payload = parts[1];
    // Handle base64url format (may need padding)
    payload = payload.replace(/-/g, '+').replace(/_/g, '/');
    // Add padding if needed
    const pad = payload.length % 4;
    if (pad) {
      payload += '='.repeat(4 - pad);
    }

    const decoded: JWTPayload = JSON.parse(atob(payload));
    return decoded.exp ?? null;
  } catch (error) {
    console.error('Failed to decode JWT token:', error);
    return null;
  }
}

/**
 * Get the configured token expiration warning threshold
 * @returns Warning threshold in seconds (default: 60)
 */
export function getTokenExpirationWarningSeconds(): number {
  const configValue = import.meta.env.VITE_TOKEN_WARNING_SECONDS;
  const parsed = parseInt(configValue, 10);
  return isNaN(parsed) ? 60 : parsed;
}

/**
 * Check if a token is expiring soon (within the warning threshold)
 * @param token JWT token string
 * @param withinSeconds Override the warning threshold (defaults to env variable or 60 seconds)
 * @returns true if token expires within the threshold, false otherwise
 */
export function isTokenExpiringSoon(
  token: string | null,
  withinSeconds?: number
): boolean {
  if (!token) return false;

  const exp = getTokenExpiration(token);
  if (!exp) return false;

  const threshold = withinSeconds ?? getTokenExpirationWarningSeconds();

  // Add clock skew buffer to account for time differences
  const now = Math.floor(Date.now() / 1000);
  return exp <= now + threshold + CLOCK_SKEW_BUFFER_SECONDS;
}
