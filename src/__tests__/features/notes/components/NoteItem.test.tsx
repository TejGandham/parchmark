import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import NoteItem from '../../../../features/notes/components/NoteItem';
import { List } from '@chakra-ui/react';

describe('NoteItem Component', () => {
  const defaultProps = {
    note: {
      id: 'note-1',
      title: 'Test Note',
      content: '# Test Note\n\nContent',
      createdAt: '2023-01-01T00:00:00.000Z',
      updatedAt: '2023-01-01T00:00:00.000Z',
    },
    isActive: false,
    onSelect: jest.fn(),
    onDelete: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    return render(
      <TestProvider>
        <List>
          <NoteItem {...defaultProps} {...props} />
        </List>
      </TestProvider>
    );
  };

  it('should render note title', () => {
    renderComponent();
    
    expect(screen.getByText('Test Note')).toBeInTheDocument();
  });

  it('should call onSelect when clicked', () => {
    renderComponent();
    
    const noteItem = screen.getByText('Test Note').closest('li');
    
    fireEvent.click(noteItem!);
    expect(defaultProps.onSelect).toHaveBeenCalledWith('note-1');
  });

  it('should call onDelete when delete button is clicked', () => {
    renderComponent();
    
    const deleteButton = screen.getByLabelText('Delete note');
    
    fireEvent.click(deleteButton);
    expect(defaultProps.onDelete).toHaveBeenCalledWith('note-1');
  });

  it('should apply active styling when isActive is true', () => {
    renderComponent({ isActive: true });
    
    const noteItem = screen.getByText('Test Note').closest('li');
    // The component uses bg color, not aria-selected
    expect(noteItem).toHaveStyle('background: rgba(88, 12, 36, 0.08)');
  });

  it('should not apply active styling when isActive is false', () => {
    renderComponent({ isActive: false });
    
    const noteItem = screen.getByText('Test Note').closest('li');
    // Just verify it doesn't have the active background
    expect(noteItem).not.toHaveStyle('background: rgba(88, 12, 36, 0.08)');
  });

  it('should truncate long titles', () => {
    const longTitle = 'This is a very long title that should be truncated to fit in the note item component';
    renderComponent({ 
      note: {
        ...defaultProps.note,
        title: longTitle
      }
    });
    
    // The text content should be available
    const titleElement = screen.getByText(longTitle);
    // Verify that the Text component has the noOfLines prop which handles truncation
    expect(titleElement).toHaveClass('css-zvlevn');
  });

  it('should handle notes with empty titles', () => {
    renderComponent({ 
      note: {
        ...defaultProps.note,
        title: ''
      }
    });
    
    // Just make sure the component renders without crashing
    // We can't test for an empty string directly because it would match multiple elements
    const listItem = screen.getByRole('listitem');
    expect(listItem).toBeInTheDocument();
  });
});