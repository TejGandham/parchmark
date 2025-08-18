import { act } from 'react';
import { useAuthStore, AuthState } from '../../../../features/auth/store/auth';
import * as api from '../../../../services/api';

jest.mock('../../../../services/api');

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
});
