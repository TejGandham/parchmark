import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    // When not authenticated, redirect to login
    return <Navigate to="/login" replace />;
  }

  // When authenticated, render children
  return <>{children}</>;
};

export default ProtectedRoute;
