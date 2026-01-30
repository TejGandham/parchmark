import * as AuthComponents from '../../../../features/auth/components/index';
import LoginForm from '../../../../features/auth/components/LoginForm';

describe('Auth Components Index', () => {
  it('should export LoginForm', () => {
    expect(AuthComponents.LoginForm).toBe(LoginForm);
  });

  it('should export all expected components', () => {
    const expectedExports = ['LoginForm', 'UserLoginStatus'];
    const actualExports = Object.keys(AuthComponents);

    expectedExports.forEach((exportName) => {
      expect(actualExports).toContain(exportName);
    });
  });
});
