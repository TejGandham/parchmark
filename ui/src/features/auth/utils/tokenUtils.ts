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
    const payload = JSON.parse(atob(base64));
    
    return payload.exp || null;
  } catch {
    return null;
  }
}

/**
 * Check if token expires within the given seconds
 * @param token - JWT token string  
 * @param withinSeconds - Check if expires within this many seconds (default: 60)
 * @returns true if token is expired or expires soon
 */
export function isTokenExpiringSoon(token: string | null, withinSeconds: number = 60): boolean {
  if (!token) return true;
  
  const exp = getTokenExpiration(token);
  if (!exp) return true;
  
  const now = Math.floor(Date.now() / 1000);
  return exp <= now + withinSeconds;
}