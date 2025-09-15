/**
 * Application constants and environment variables
 * This file abstracts Vite's import.meta.env for easier testing
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Auth Configuration
export const TOKEN_WARNING_SECONDS = import.meta.env.VITE_TOKEN_WARNING_SECONDS;

// Other environment variables can be added here as needed
export const IS_PRODUCTION = import.meta.env.PROD;
export const IS_DEVELOPMENT = import.meta.env.DEV;
