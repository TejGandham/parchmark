import { describe, it, expect, vi, afterEach } from 'vitest';

const loadConstants = async () => {
  vi.resetModules();
  return import('../../config/constants');
};

describe('config/constants', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('falls back to /api when VITE_API_URL is not provided', async () => {
    vi.stubEnv('VITE_API_URL', '');

    const constants = await loadConstants();

    expect(constants.API_BASE_URL).toBe('/api');
  });

  it('mirrors the existing environment flags', async () => {
    const constants = await loadConstants();

    expect(constants.TOKEN_WARNING_SECONDS).toBe(
      import.meta.env.VITE_TOKEN_WARNING_SECONDS
    );
    expect(constants.IS_PRODUCTION).toBe(import.meta.env.PROD);
    expect(constants.IS_DEVELOPMENT).toBe(import.meta.env.DEV);
  });
});
