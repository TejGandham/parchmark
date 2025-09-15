import { useEffect } from 'react';
import { useAuthStore } from '../store';

/**
 * Hook to monitor JWT token expiration and logout automatically
 * Checks every 30 seconds if token expires within the next minute
 */
export function useTokenExpirationMonitor() {
  const token = useAuthStore((state) => state.token);
  const checkTokenExpiration = useAuthStore((state) => state.actions.checkTokenExpiration);

  useEffect(() => {
    if (!token) return;

    // Check immediately
    checkTokenExpiration();

    // Check every 30 seconds
    const interval = setInterval(checkTokenExpiration, 30000);

    return () => clearInterval(interval);
  }, [token, checkTokenExpiration]);
}