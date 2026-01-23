import type mermaidType from 'mermaid';

let mermaidInstance: typeof mermaidType | null = null;
let initPromise: Promise<typeof mermaidType> | null = null;

/**
 * Lazily loads and initializes mermaid library.
 * Returns the mermaid instance ready for use.
 */
export const getMermaid = async (): Promise<typeof mermaidType> => {
  if (mermaidInstance) return mermaidInstance;

  if (!initPromise) {
    initPromise = import('mermaid').then((module) => {
      mermaidInstance = module.default;
      mermaidInstance.initialize({
        startOnLoad: true, // Required for contentLoaded() to work
        theme: 'default',
        securityLevel: 'loose',
      });
      return mermaidInstance;
    });
  }

  return initPromise;
};
