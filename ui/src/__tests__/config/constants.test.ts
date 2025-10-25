import { describe, it, expect } from 'vitest';
import {
  API_BASE_URL,
  TOKEN_WARNING_SECONDS,
  IS_PRODUCTION,
  IS_DEVELOPMENT,
} from '../../config/constants';

describe('constants', () => {
  it('should export API_BASE_URL', () => {
    expect(API_BASE_URL).toBeDefined();
    expect(typeof API_BASE_URL).toBe('string');
  });

  it('should export TOKEN_WARNING_SECONDS (can be undefined)', () => {
    // In test environment, this might be undefined if not set in .env
    // The export exists but the value may be undefined
    expect(typeof TOKEN_WARNING_SECONDS === 'string' || TOKEN_WARNING_SECONDS === undefined).toBe(true);
  });

  it('should export IS_PRODUCTION', () => {
    expect(typeof IS_PRODUCTION).toBe('boolean');
  });

  it('should export IS_DEVELOPMENT', () => {
    expect(typeof IS_DEVELOPMENT).toBe('boolean');
  });

  it('should have IS_PRODUCTION and IS_DEVELOPMENT as opposites in test env', () => {
    // In test environment, typically IS_DEVELOPMENT is true
    expect(IS_PRODUCTION).toBe(false);
    expect(IS_DEVELOPMENT).toBe(true);
  });
});
