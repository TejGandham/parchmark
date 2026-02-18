import type mermaidType from 'mermaid';

let mermaidInstance: typeof mermaidType | null = null;
let initPromise: Promise<typeof mermaidType> | null = null;

/**
 * Lazily loads and initializes mermaid library.
 * Returns the mermaid instance ready for use.
 *
 * startOnLoad is false — components call mermaid.render() directly.
 * Theme is set per-render so it can react to color mode changes.
 */
export const getMermaid = async (): Promise<typeof mermaidType> => {
  if (mermaidInstance) return mermaidInstance;

  if (!initPromise) {
    initPromise = import('mermaid').then((module) => {
      mermaidInstance = module.default;
      mermaidInstance.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
      });
      return mermaidInstance;
    });
  }

  return initPromise;
};
