import { act } from 'react';
import { useAuthStore, AuthState } from '../../../../features/auth/store/auth';
import * as api from '../../../../services/api';
import * as tokenUtils from '../../../../features/auth/utils/tokenUtils';

jest.mock('../../../../services/api');
jest.mock('../../../../features/auth/utils/tokenUtils');

describe('Auth Store', () => {
  let store: AuthState;

  beforeEach(() => {
    // Reset the store before each test
    act(() => {
      useAuthStore.setState({
        isAuthenticated: false,
        user: null,
        token: null,
        error: null,
        actions: useAuthStore.getState().actions,
      });
    });

    store = useAuthStore.getState();
    jest.clearAllMocks();
  });

  it('should initialize with unauthenticated state', () => {
    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
    expect(store.error).toBeNull();
  });

  it('should authenticate with valid credentials', async () => {
    const { actions } = store;

    // Mock the successful API call
    (api.login as jest.Mock).mockResolvedValue({ access_token: 'test-token' });

    const success = await actions.login('user', 'password');
    const newState = useAuthStore.getState();

    expect(success).toBe(true);
    expect(newState.isAuthenticated).toBe(true);
    expect(newState.user).toEqual({ username: 'user', password: '' });
    expect(newState.error).toBeNull();
  });

  it('should fail authentication with invalid credentials', async () => {
    const { actions } = store;

    // Mock the failed API call
    (api.login as jest.Mock).mockRejectedValue(
      new Error('Invalid username or password')
    );

    const success = await actions.login('user', 'wrongpassword');
    const newState = useAuthStore.getState();

    expect(success).toBe(false);
    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.error).toBe('Invalid username or password');
  });

  it('should handle login error without message', async () => {
    const { actions } = store;

    // Mock the failed API call with error object without message
    (api.login as jest.Mock).mockRejectedValue({});

    const success = await actions.login('user', 'wrongpassword');
    const newState = useAuthStore.getState();

    expect(success).toBe(false);
    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.error).toBe('Login failed');
  });

  it('should logout successfully', async () => {
    const { actions } = store;

    // First login
    (api.login as jest.Mock).mockResolvedValue({ access_token: 'test-token' });
    await actions.login('user', 'password');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    // Then logout
    actions.logout();
    const newState = useAuthStore.getState();

    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.token).toBeNull();
  });

  it('should clear error message', async () => {
    const { actions } = store;

    // First create an error
    (api.login as jest.Mock).mockRejectedValue(
      new Error('Invalid username or password')
    );
    await actions.login('user', 'wrongpassword');
    expect(useAuthStore.getState().error).toBe('Invalid username or password');

    // Then clear the error
    actions.clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });

  describe('checkTokenExpiration', () => {
    it('should logout when token is expiring soon', async () => {
      const { actions } = store;

      // First login to set a token
      (api.login as jest.Mock).mockResolvedValue({ access_token: 'test-token' });
      await actions.login('user', 'password');
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().token).toBe('test-token');

      // Mock token as expiring soon
      (tokenUtils.isTokenExpiringSoon as jest.Mock).mockReturnValue(true);

      // Check token expiration
      actions.checkTokenExpiration();

      // Should logout
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.user).toBeNull();
      expect(newState.token).toBeNull();
    });

    it('should not logout when token is not expiring soon', async () => {
      const { actions } = store;

      // First login to set a token
      (api.login as jest.Mock).mockResolvedValue({ access_token: 'test-token' });
      await actions.login('user', 'password');
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Mock token as not expiring soon
      (tokenUtils.isTokenExpiringSoon as jest.Mock).mockReturnValue(false);

      // Check token expiration
      actions.checkTokenExpiration();

      // Should remain logged in
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.user).toEqual({ username: 'user', password: '' });
      expect(newState.token).toBe('test-token');
    });

    it('should handle null token gracefully', () => {
      const { actions } = store;

      // Ensure no token is set
      expect(useAuthStore.getState().token).toBeNull();

      // Mock isTokenExpiringSoon to return true for null
      (tokenUtils.isTokenExpiringSoon as jest.Mock).mockReturnValue(true);

      // Check token expiration
      actions.checkTokenExpiration();

      // Should call logout but state is already logged out
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.token).toBeNull();
    });
  });

  describe('onRehydrateStorage', () => {
    it('should logout on rehydration if token is expiring', () => {
      // Mock isTokenExpiringSoon to return true
      (tokenUtils.isTokenExpiringSoon as jest.Mock).mockReturnValue(true);

      // Simulate rehydration with an expiring token
      const mockState = {
        isAuthenticated: true,
        user: { username: 'testuser', password: '' },
        token: 'expiring-token',
        error: null,
        actions: useAuthStore.getState().actions,
      };

      // Access the persist configuration
      const persistConfig = (useAuthStore as any).persist;
      const onRehydrateCallback = persistConfig.onRehydrateStorage();
      
      // Call the rehydration callback
      act(() => {
        onRehydrateCallback(mockState);
      });

      // Verify that logout was called
      expect(mockState.isAuthenticated).toBe(false);
      expect(mockState.token).toBeNull();
      expect(mockState.user).toBeNull();
    });

    it('should not logout on rehydration if token is valid', () => {
      // Mock isTokenExpiringSoon to return false
      (tokenUtils.isTokenExpiringSoon as jest.Mock).mockReturnValue(false);

      // Simulate rehydration with a valid token
      const mockState = {
        isAuthenticated: true,
        user: { username: 'testuser', password: '' },
        token: 'valid-token',
        error: null,
        actions: useAuthStore.getState().actions,
      };

      // Access the persist configuration
      const persistConfig = (useAuthStore as any).persist;
      const onRehydrateCallback = persistConfig.onRehydrateStorage();
      
      // Call the rehydration callback
      act(() => {
        onRehydrateCallback(mockState);
      });

      // Verify that state remains unchanged
      expect(mockState.isAuthenticated).toBe(true);
      expect(mockState.token).toBe('valid-token');
      expect(mockState.user).toEqual({ username: 'testuser', password: '' });
    });

    it('should handle rehydration with no token', () => {
      // Simulate rehydration with no token
      const mockState = {
        isAuthenticated: false,
        user: null,
        token: null,
        error: null,
        actions: useAuthStore.getState().actions,
      };

      // Access the persist configuration
      const persistConfig = (useAuthStore as any).persist;
      const onRehydrateCallback = persistConfig.onRehydrateStorage();
      
      // Call the rehydration callback
      act(() => {
        onRehydrateCallback(mockState);
      });

      // Verify that isTokenExpiringSoon was not called (no token to check)
      expect(tokenUtils.isTokenExpiringSoon).not.toHaveBeenCalled();
    });
  });
});
