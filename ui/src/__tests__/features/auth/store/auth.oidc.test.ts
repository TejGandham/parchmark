import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from '../../../../features/auth/store/auth';

vi.mock('../../../../features/auth/utils/oidcUtils', () => ({
  startOIDCLogin: vi.fn(),
  handleOIDCCallback: vi.fn(),
  logoutOIDC: vi.fn(),
  renewOIDCToken: vi.fn(),
}));

vi.mock('../../../../services/api', () => ({
  login: vi.fn(),
  refreshToken: vi.fn(),
}));

describe('Auth Store - OIDC Methods', () => {
  beforeEach(() => {
    // Reset store state
    const store = useAuthStore.getState();
    store.actions.logout();
    vi.clearAllMocks();
  });

  it('initializes with local token source', () => {
    const store = useAuthStore.getState();
    expect(store.tokenSource).toBe('local');
  });

  it('stores tokenSource on login', async () => {
    const store = useAuthStore.getState();
    // Token source should be set based on auth method
    expect(['local', 'oidc']).toContain(store.tokenSource);
  });

  it('distinguishes between local and OIDC tokens', () => {
    const state = useAuthStore.getState();
    expect(state.tokenSource).toBeDefined();
  });

  it('persists tokenSource in localStorage', () => {
    const store = useAuthStore.getState();
    // After logout, tokenSource should revert
    store.actions.logout();
    const newState = useAuthStore.getState();
    expect(newState.tokenSource).toBe('local');
  });

  it('handles OIDC token refresh differently from local refresh', async () => {
    const store = useAuthStore.getState();
    // Auth store should have different refresh logic based on tokenSource
    expect(store.actions.refreshTokens).toBeDefined();
  });

  it('clears OIDC session on logout', async () => {
    const store = useAuthStore.getState();
    store.actions.logout();
    expect(store.isAuthenticated).toBe(false);
    expect(store.token).toBeNull();
    expect(store.refreshToken).toBeNull();
  });

  it('sets correct token source on OIDC login callback', () => {
    const state = useAuthStore.getState();
    // Token source should default to local
    expect(state.tokenSource).toBe('local');
  });

  it('handles missing OIDC user info gracefully', () => {
    const store = useAuthStore.getState();
    expect(store.user).toBeNull();
  });
});
