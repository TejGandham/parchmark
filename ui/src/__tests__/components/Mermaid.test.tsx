import { vi, beforeEach, describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

const { mockRender, mockInitialize } = vi.hoisted(() => ({
  mockRender: vi.fn(),
  mockInitialize: vi.fn(),
}));

vi.mock('mermaid', () => ({
  default: {
    initialize: () => {},
    render: () => Promise.resolve({ svg: '<svg></svg>' }),
  },
}));

vi.mock('../../utils/mermaidInit', () => ({
  getMermaid: async () => ({
    render: (...args: unknown[]) => mockRender(...args),
    initialize: mockInitialize,
  }),
}));

vi.mock('@chakra-ui/react', async () => {
  const actual = await vi.importActual('@chakra-ui/react');
  return {
    ...(actual as Record<string, unknown>),
    useColorMode: () => ({ colorMode: 'light', toggleColorMode: vi.fn() }),
  };
});

import Mermaid from '../../components/Mermaid';

describe('Mermaid Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRender.mockResolvedValue({
      svg: '<svg class="mermaid-svg">rendered</svg>',
    });
  });

  it('should call mermaid.render() with a unique ID and chart content', async () => {
    render(<Mermaid chart="graph TD; A-->B;" />);

    await waitFor(() => {
      expect(mockRender).toHaveBeenCalledWith(
        expect.stringMatching(/^mermaid-\d+$/),
        'graph TD; A-->B;'
      );
    });
  });

  it('should insert rendered SVG into the DOM', async () => {
    mockRender.mockResolvedValue({
      svg: '<svg data-testid="rendered-diagram">diagram</svg>',
    });
    render(<Mermaid chart="graph TD; A-->B;" />);

    await waitFor(() => {
      const svgElement = document.querySelector(
        'svg[data-testid="rendered-diagram"]'
      );
      expect(svgElement).toBeInTheDocument();
    });
  });

  it('should initialize mermaid with light theme by default', async () => {
    render(<Mermaid chart="graph TD; A-->B;" />);

    await waitFor(() => {
      expect(mockInitialize).toHaveBeenCalledWith({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
      });
    });
  });

  it('should generate unique IDs for multiple diagrams', async () => {
    render(
      <>
        <Mermaid chart="graph TD; A-->B;" />
        <Mermaid chart="graph TD; C-->D;" />
      </>
    );

    await waitFor(() => {
      expect(mockRender).toHaveBeenCalledTimes(2);
    });

    const ids = mockRender.mock.calls.map(
      (call: unknown[]) => call[0] as string
    );
    expect(ids[0]).not.toBe(ids[1]);
  });

  it('should re-render when chart content changes', async () => {
    const { rerender } = render(
      <Mermaid chart="flowchart TD; Start --> Stop;" />
    );

    await waitFor(() => {
      expect(mockRender).toHaveBeenCalled();
    });

    mockRender.mockClear();
    rerender(<Mermaid chart="sequenceDiagram; Alice->>Bob: Hello Bob;" />);

    await waitFor(() => {
      expect(mockRender).toHaveBeenCalledWith(
        expect.stringMatching(/^mermaid-\d+$/),
        'sequenceDiagram; Alice->>Bob: Hello Bob;'
      );
    });
  });

  it('should not render empty chart content', async () => {
    render(<Mermaid chart="" />);

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(mockRender).not.toHaveBeenCalled();
  });

  it('should display error state when render fails', async () => {
    mockRender.mockRejectedValueOnce(new Error('Parse error'));

    render(<Mermaid chart="invalid mermaid syntax" />);

    await waitFor(() => {
      expect(screen.getByText(/Diagram error:/)).toBeInTheDocument();
      expect(screen.getByText(/Parse error/)).toBeInTheDocument();
    });
  });

  it('should show raw chart source in error state', async () => {
    mockRender.mockRejectedValueOnce(new Error('Bad syntax'));

    render(<Mermaid chart="broken---diagram" />);

    await waitFor(() => {
      expect(screen.getByText('broken---diagram')).toBeInTheDocument();
    });
  });
});
