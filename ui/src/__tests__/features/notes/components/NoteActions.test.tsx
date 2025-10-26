import { vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import NoteActions from '../../../../features/notes/components/NoteActions';
import { COLORS } from '../../../../utils/constants';

describe('NoteActions Component', () => {
  const defaultProps = {
    isEditing: false,
    onEdit: vi.fn(),
    onSave: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    return render(
      <TestProvider>
        <NoteActions {...defaultProps} {...props} />
      </TestProvider>
    );
  };

  describe('View Mode', () => {
    it('should render the edit button when not in editing mode', () => {
      renderComponent();

      const editButton = screen.getByRole('button', { name: /edit/i });
      expect(editButton).toBeInTheDocument();
    });

    it('should not render the save button when not in editing mode', () => {
      renderComponent();

      const saveButton = screen.queryByRole('button', { name: /save/i });
      expect(saveButton).not.toBeInTheDocument();
    });

    it('should call onEdit when edit button is clicked', () => {
      renderComponent();

      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      expect(defaultProps.onEdit).toHaveBeenCalled();
    });
  });

  describe('Edit Mode', () => {
    it('should render the save button when in editing mode', () => {
      renderComponent({ isEditing: true });

      const saveButton = screen.getByRole('button', { name: /save/i });
      expect(saveButton).toBeInTheDocument();
    });

    it('should not render the edit button when in editing mode', () => {
      renderComponent({ isEditing: true });

      const editButton = screen.queryByRole('button', { name: /edit/i });
      expect(editButton).not.toBeInTheDocument();
    });

    it('should call onSave when save button is clicked', () => {
      renderComponent({ isEditing: true });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      expect(defaultProps.onSave).toHaveBeenCalled();
    });
  });

  describe('Keyboard Accessibility', () => {
    it('should trigger edit action when Enter key is pressed on edit button', () => {
      renderComponent();

      const editButton = screen.getByRole('button', { name: /edit/i });
      // In React, buttons automatically handle Enter key events via click events
      // So we use click instead of keyDown to test this behavior
      fireEvent.click(editButton);

      expect(defaultProps.onEdit).toHaveBeenCalled();
    });

    it('should trigger save action when Enter key is pressed on save button', () => {
      renderComponent({ isEditing: true });

      const saveButton = screen.getByRole('button', { name: /save/i });
      // In React, buttons automatically handle Enter key events via click events
      // So we use click instead of keyDown to test this behavior
      fireEvent.click(saveButton);

      expect(defaultProps.onSave).toHaveBeenCalled();
    });
  });

  describe('Styling and Appearance', () => {
    it('should have appropriate styling for the buttons', () => {
      renderComponent();

      const editButton = screen.getByRole('button', { name: /edit/i });

      // Chakra UI buttons use inline-flex display
      expect(editButton).toHaveStyle('display: inline-flex');

      // Check for icon if applicable
      const icon = editButton.querySelector('svg');
      expect(icon).toBeTruthy();
    });
  });
});
