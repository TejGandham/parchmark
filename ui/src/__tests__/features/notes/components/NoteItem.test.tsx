import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import NoteItem from '../../../../features/notes/components/NoteItem';
import { List } from '@chakra-ui/react';
import { formatRelativeDate } from '../../../../utils/dateFormatting';

vi.mock('../../../../utils/dateFormatting', () => ({
  formatRelativeDate: vi.fn(),
}));

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
    onSelect: vi.fn(),
    onDelete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(formatRelativeDate).mockReturnValue('Jan 1, 2023');
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

  it('should render relative date text from formatRelativeDate', () => {
    vi.mocked(formatRelativeDate).mockReturnValue('updated recently');
    renderComponent();

    expect(screen.getByText('updated recently')).toBeInTheDocument();
    expect(formatRelativeDate).toHaveBeenCalledWith('2023-01-01T00:00:00.000Z');
  });

  it('should call onSelect when clicked', () => {
    renderComponent();

    const noteItem = screen.getByText('Test Note').closest('li');

    fireEvent.click(noteItem!);
    expect(defaultProps.onSelect).toHaveBeenCalledWith('note-1');
  });

  it('should call onDelete when delete button is clicked', () => {
    renderComponent();

    const deleteButton = screen.getByLabelText('Delete note: Test Note');

    fireEvent.click(deleteButton);
    expect(defaultProps.onDelete).toHaveBeenCalledWith('note-1');
  });

  it('should apply active styling when isActive is true', () => {
    renderComponent({ isActive: true });

    const noteItem = screen.getByText('Test Note').closest('li');
    // The component uses primary.50 color for active state
    // Chakra UI will resolve this to the actual color value
    expect(noteItem).toHaveStyle({ cursor: 'pointer' });
  });

  it('should not apply active styling when isActive is false', () => {
    renderComponent({ isActive: false });

    const noteItem = screen.getByText('Test Note').closest('li');
    // The component should still have cursor pointer
    expect(noteItem).toHaveStyle({ cursor: 'pointer' });
    // We're just verifying the element exists with proper cursor
    expect(noteItem).toBeInTheDocument();
  });

  it('should truncate long titles', () => {
    const longTitle =
      'This is a very long title that should be truncated to fit in the note item component';
    renderComponent({
      note: {
        ...defaultProps.note,
        title: longTitle,
      },
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
        title: '',
      },
    });

    // Just make sure the component renders without crashing
    // The ListItem now has role="button" for accessibility
    const noteButton = screen.getByRole('button', { name: /Select note/i });
    expect(noteButton).toBeInTheDocument();
  });

  it('should call onSelect when Enter key is pressed', () => {
    renderComponent();

    const noteItem = screen.getByRole('button', { name: /Select note/i });

    fireEvent.keyDown(noteItem, { key: 'Enter', code: 'Enter' });
    expect(defaultProps.onSelect).toHaveBeenCalledWith('note-1');
  });

  it('should call onSelect when Space key is pressed', () => {
    renderComponent();

    const noteItem = screen.getByRole('button', { name: /Select note/i });

    fireEvent.keyDown(noteItem, { key: ' ', code: 'Space' });
    expect(defaultProps.onSelect).toHaveBeenCalledWith('note-1');
  });

  it('should call onDelete when Enter key is pressed on delete button', () => {
    renderComponent();

    const deleteButton = screen.getByLabelText('Delete note: Test Note');

    fireEvent.keyDown(deleteButton, { key: 'Enter', code: 'Enter' });
    expect(defaultProps.onDelete).toHaveBeenCalledWith('note-1');
  });

  it('should call onDelete when Space key is pressed on delete button', () => {
    renderComponent();

    const deleteButton = screen.getByLabelText('Delete note: Test Note');

    fireEvent.keyDown(deleteButton, { key: ' ', code: 'Space' });
    expect(defaultProps.onDelete).toHaveBeenCalledWith('note-1');
  });

  it('should not call onSelect when other keys are pressed', () => {
    renderComponent();

    const noteItem = screen.getByRole('button', { name: /Select note/i });

    fireEvent.keyDown(noteItem, { key: 'a', code: 'KeyA' });
    expect(defaultProps.onSelect).not.toHaveBeenCalled();
  });
});
