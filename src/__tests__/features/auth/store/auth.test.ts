import { useAuthStore } from '../../../../features/auth/store';

// Create a test wrapper to avoid persistence in tests
const createTestStore = () => {
  // Clear any persisted state to avoid test interference
  localStorage.removeItem('parchmark-auth');

  // Get a fresh instance of the store
  return useAuthStore;
};

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store before each test
    const store = createTestStore();
    store.setState({
      isAuthenticated: false,
      user: null,
      error: null,
    });
  });

  it('should initialize with unauthenticated state', () => {
    const store = createTestStore();
    const state = store.getState();

    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.error).toBeNull();
  });

  it('should authenticate with valid credentials', () => {
    const store = createTestStore();
    const { actions } = store.getState();

    const success = actions.login('user', 'password');
    const newState = store.getState();

    expect(success).toBe(true);
    expect(newState.isAuthenticated).toBe(true);
    expect(newState.user).toEqual({ username: 'user', password: '' });
    expect(newState.error).toBeNull();
  });

  it('should fail authentication with invalid credentials', () => {
    const store = createTestStore();
    const { actions } = store.getState();

    const success = actions.login('user', 'wrongpassword');
    const newState = store.getState();

    expect(success).toBe(false);
    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.error).toBe('Invalid username or password');
  });

  it('should logout successfully', () => {
    const store = createTestStore();
    const { actions } = store.getState();

    // First login
    actions.login('user', 'password');
    expect(store.getState().isAuthenticated).toBe(true);

    // Then logout
    actions.logout();
    const newState = store.getState();

    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.error).toBeNull();
  });

  it('should clear error message', () => {
    const store = createTestStore();
    const { actions } = store.getState();

    // First create an error
    actions.login('user', 'wrongpassword');
    expect(store.getState().error).toBe('Invalid username or password');

    // Then clear the error
    actions.clearError();
    expect(store.getState().error).toBeNull();
  });
});
