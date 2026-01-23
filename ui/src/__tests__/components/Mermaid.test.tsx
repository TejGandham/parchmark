import { vi, beforeEach, describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Use vi.hoisted to create mock functions that can be referenced in vi.mock
const { mockContentLoaded, mockInitialize } = vi.hoisted(() => ({
  mockContentLoaded: vi.fn(),
  mockInitialize: vi.fn(),
}));

// Mock mermaid library - must happen before import
vi.mock('mermaid', () => ({
  default: {
    initialize: () => {},
    contentLoaded: () => Promise.resolve(),
  },
}));

// Mock mermaidInit module with lazy loading API
vi.mock('../../utils/mermaidInit', () => ({
  getMermaid: async () => {
    mockInitialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
    });
    return {
      contentLoaded: (...args: unknown[]) => mockContentLoaded(...args),
      initialize: mockInitialize,
    };
  },
}));

// Import component after mocks are set up
import Mermaid from '../../components/Mermaid';

describe('Mermaid Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset contentLoaded to resolve successfully
    mockContentLoaded.mockResolvedValue(undefined);
  });

  it('should render mermaid chart container with mermaid class', async () => {
    const chartContent = 'graph TD; A-->B;';
    render(<Mermaid chart={chartContent} />);

    await waitFor(() => {
      expect(mockContentLoaded).toHaveBeenCalled();
    });

    // Check that the container has the mermaid class
    const container = document.querySelector('.mermaid');
    expect(container).toBeInTheDocument();
    expect(container).toHaveTextContent(chartContent);
  });

  it('should initialize mermaid with correct configuration', async () => {
    render(<Mermaid chart="graph TD; A-->B;" />);

    await waitFor(() => {
      expect(mockInitialize).toHaveBeenCalledWith({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
      });
    });
  });

  it('should call mermaid.contentLoaded to render diagrams', async () => {
    const chartContent = 'graph TD; A-->B;';
    render(<Mermaid chart={chartContent} />);

    await waitFor(() => {
      expect(mockContentLoaded).toHaveBeenCalled();
    });
  });

  it('should render different chart types', async () => {
    const flowchartContent = 'flowchart TD; Start --> Stop;';
    const { rerender } = render(<Mermaid chart={flowchartContent} />);

    await waitFor(() => {
      expect(mockContentLoaded).toHaveBeenCalled();
    });

    mockContentLoaded.mockClear();

    const sequenceContent = 'sequenceDiagram; Alice->>Bob: Hello Bob;';
    rerender(<Mermaid chart={sequenceContent} />);

    await waitFor(() => {
      expect(mockContentLoaded).toHaveBeenCalled();
    });
  });

  it('should not render empty chart content', async () => {
    render(<Mermaid chart="" />);

    // Give it a moment to potentially call contentLoaded
    await new Promise((resolve) => setTimeout(resolve, 50));

    // Empty chart should not trigger contentLoaded
    expect(mockContentLoaded).not.toHaveBeenCalled();
  });

  it('should display error state when render fails', async () => {
    mockContentLoaded.mockRejectedValueOnce(new Error('Parse error'));

    render(<Mermaid chart="invalid mermaid syntax" />);

    await waitFor(() => {
      expect(screen.getByText(/Diagram error:/)).toBeInTheDocument();
      expect(screen.getByText(/Parse error/)).toBeInTheDocument();
    });
  });
});
