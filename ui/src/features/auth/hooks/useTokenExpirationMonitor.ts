import { useEffect } from 'react';
import { useAuthStore } from '../store';

/**
 * Hook to monitor JWT token expiration and logout automatically
 * Checks every 3 minutes if token expires within the next minute
 */
export function useTokenExpirationMonitor() {
  const token = useAuthStore((state) => state.token);
  const checkTokenExpiration = useAuthStore((state) => state.actions.checkTokenExpiration);

  useEffect(() => {
    if (!token) return;

    // Check immediately
    checkTokenExpiration();

    // Check every 3 minutes (180 seconds)
    const interval = setInterval(checkTokenExpiration, 180000);

    return () => clearInterval(interval);
  }, [token, checkTokenExpiration]);
}