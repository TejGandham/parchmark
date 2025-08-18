import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import Mermaid from '../../components/Mermaid';

// Mock mermaid library
jest.mock('mermaid', () => ({
  initialize: jest.fn(),
  contentLoaded: jest.fn(),
}));

const mermaidMock = require('mermaid');

describe('Mermaid Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render mermaid chart content', () => {
    const chartContent = 'graph TD; A-->B;';
    const { container } = render(<Mermaid chart={chartContent} />);

    const mermaidDiv = container.querySelector('.mermaid');
    expect(mermaidDiv).toBeInTheDocument();
    expect(mermaidDiv).toHaveTextContent(chartContent);
  });

  it('should initialize mermaid with correct configuration', () => {
    render(<Mermaid chart="graph TD; A-->B;" />);

    expect(mermaidMock.initialize).toHaveBeenCalledWith({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
    });
  });

  it('should call contentLoaded after initialization', () => {
    render(<Mermaid chart="graph TD; A-->B;" />);

    expect(mermaidMock.contentLoaded).toHaveBeenCalled();
  });

  it('should render different chart types', () => {
    const flowchartContent = 'flowchart TD; Start --> Stop;';
    const { rerender, container } = render(
      <Mermaid chart={flowchartContent} />
    );

    expect(container.querySelector('.mermaid')).toHaveTextContent(
      flowchartContent
    );

    const sequenceContent = 'sequenceDiagram; Alice->>Bob: Hello Bob;';
    rerender(<Mermaid chart={sequenceContent} />);

    expect(container.querySelector('.mermaid')).toHaveTextContent(
      sequenceContent
    );
  });

  it('should handle empty chart content', () => {
    const { container } = render(<Mermaid chart="" />);

    const mermaidDiv = container.querySelector('.mermaid');
    expect(mermaidDiv).toBeInTheDocument();
    expect(mermaidDiv).toHaveTextContent('');
  });

  it('should initialize mermaid only once per component instance', () => {
    const { rerender } = render(<Mermaid chart="graph TD; A-->B;" />);

    expect(mermaidMock.initialize).toHaveBeenCalledTimes(1);
    expect(mermaidMock.contentLoaded).toHaveBeenCalledTimes(1);

    // Rerender with different chart - should not call initialize again
    rerender(<Mermaid chart="graph TD; B-->C;" />);

    expect(mermaidMock.initialize).toHaveBeenCalledTimes(1);
    expect(mermaidMock.contentLoaded).toHaveBeenCalledTimes(1);
  });
});
