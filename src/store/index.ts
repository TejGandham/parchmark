/**
 * Central store index that automatically re-exports all stores from feature modules.
 *
 * This file serves as the single entry point for accessing all stores in the application.
 * When adding a new feature with a store, simply create a barrel file in that feature's
 * store directory and it will be automatically included here.
 */

// Import from feature barrel files instead of individual store files
export * from '../features/notes/store';
export * from '../features/ui/store';
