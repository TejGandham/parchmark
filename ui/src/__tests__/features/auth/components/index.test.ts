import * as AuthComponents from '../../../../features/auth/components/index';
import LoginForm from '../../../../features/auth/components/LoginForm';
import ProtectedRoute from '../../../../features/auth/components/ProtectedRoute';

describe('Auth Components Index', () => {
  it('should export LoginForm', () => {
    expect(AuthComponents.LoginForm).toBe(LoginForm);
  });

  it('should export ProtectedRoute', () => {
    expect(AuthComponents.ProtectedRoute).toBe(ProtectedRoute);
  });

  it('should export all expected components', () => {
    const expectedExports = ['LoginForm', 'ProtectedRoute'];
    const actualExports = Object.keys(AuthComponents);
    
    expectedExports.forEach(exportName => {
      expect(actualExports).toContain(exportName);
    });
  });
});