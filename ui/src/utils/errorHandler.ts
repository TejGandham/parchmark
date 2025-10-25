// Common error codes for the application
export const ERROR_CODES = {
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  SERVER_ERROR: 'SERVER_ERROR',
  PARSE_ERROR: 'PARSE_ERROR',
  TYPE_ERROR: 'TYPE_ERROR',
} as const;

export type ErrorCode = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: ErrorCode,
    public readonly statusCode?: number,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export const handleError = (error: unknown): AppError => {
  if (error instanceof AppError) return error;

  // Handle specific Error types with more specific codes
  if (error instanceof TypeError) {
    return new AppError(error.message, ERROR_CODES.TYPE_ERROR);
  }

  if (error instanceof SyntaxError) {
    return new AppError(error.message, ERROR_CODES.PARSE_ERROR);
  }

  if (error instanceof Error) {
    // Check for network errors
    if (error.message.includes('fetch') || error.message.includes('network')) {
      return new AppError(error.message, ERROR_CODES.NETWORK_ERROR);
    }
    return new AppError(error.message, ERROR_CODES.UNKNOWN_ERROR);
  }

  return new AppError(
    'An unexpected error occurred',
    ERROR_CODES.UNKNOWN_ERROR
  );
};
