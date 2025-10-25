import { describe, it, expect } from 'vitest';
import { AppError, handleError } from '../../utils/errorHandler';

describe('AppError', () => {
  it('should create an AppError with message and code', () => {
    const error = new AppError('Test error', 'TEST_CODE');

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(AppError);
    expect(error.message).toBe('Test error');
    expect(error.code).toBe('TEST_CODE');
    expect(error.name).toBe('AppError');
  });

  it('should create an AppError with status code', () => {
    const error = new AppError('Test error', 'TEST_CODE', 404);

    expect(error.statusCode).toBe(404);
  });

  it('should create an AppError with context', () => {
    const context = { userId: '123', action: 'login' };
    const error = new AppError('Test error', 'TEST_CODE', 400, context);

    expect(error.context).toEqual(context);
  });

  it('should create an AppError without optional parameters', () => {
    const error = new AppError('Test error', 'TEST_CODE');

    expect(error.statusCode).toBeUndefined();
    expect(error.context).toBeUndefined();
  });

  it('should have correct stack trace', () => {
    const error = new AppError('Test error', 'TEST_CODE');

    expect(error.stack).toBeDefined();
    expect(error.stack).toContain('AppError');
  });
});

describe('handleError', () => {
  it('should return AppError unchanged', () => {
    const appError = new AppError('Test error', 'TEST_CODE', 400);
    const result = handleError(appError);

    expect(result).toBe(appError);
    expect(result.message).toBe('Test error');
    expect(result.code).toBe('TEST_CODE');
    expect(result.statusCode).toBe(400);
  });

  it('should convert Error to AppError', () => {
    const error = new Error('Standard error');
    const result = handleError(error);

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('Standard error');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should convert TypeError to AppError', () => {
    const error = new TypeError('Type error');
    const result = handleError(error);

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('Type error');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should handle string errors', () => {
    const result = handleError('String error');

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('An unexpected error occurred');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should handle null errors', () => {
    const result = handleError(null);

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('An unexpected error occurred');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should handle undefined errors', () => {
    const result = handleError(undefined);

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('An unexpected error occurred');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should handle object errors', () => {
    const result = handleError({ foo: 'bar' });

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('An unexpected error occurred');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should handle number errors', () => {
    const result = handleError(404);

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('An unexpected error occurred');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });

  it('should preserve Error subclass messages', () => {
    class CustomError extends Error {
      constructor(message: string) {
        super(message);
        this.name = 'CustomError';
      }
    }

    const error = new CustomError('Custom error message');
    const result = handleError(error);

    expect(result).toBeInstanceOf(AppError);
    expect(result.message).toBe('Custom error message');
    expect(result.code).toBe('UNKNOWN_ERROR');
  });
});
