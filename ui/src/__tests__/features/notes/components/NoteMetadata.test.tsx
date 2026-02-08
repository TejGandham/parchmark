import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import NoteMetadata from '../../../../features/notes/components/NoteMetadata';
import { TestProvider } from '../../../__mocks__/testUtils';
import {
  datesAreDifferent,
  formatFullDate,
  formatRelativeDate,
} from '../../../../utils/dateFormatting';

vi.mock('../../../../utils/dateFormatting', () => ({
  formatRelativeDate: vi.fn(),
  formatFullDate: vi.fn(),
  datesAreDifferent: vi.fn(),
}));

describe('NoteMetadata', () => {
  const createdAt = '2026-02-05T10:00:00.000Z';
  const updatedAt = '2026-02-07T10:00:00.000Z';

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(formatRelativeDate).mockImplementation((iso: string) =>
      iso === createdAt ? '2 days ago' : '3 hours ago'
    );
    vi.mocked(formatFullDate).mockImplementation((iso: string) =>
      iso === createdAt
        ? 'February 5, 2026 at 10:00 AM'
        : 'February 7, 2026 at 10:00 AM'
    );
    vi.mocked(datesAreDifferent).mockReturnValue(true);
  });

  const renderComponent = (props?: {
    createdAt?: string;
    updatedAt?: string;
  }) => {
    return render(
      <TestProvider>
        <NoteMetadata
          createdAt={props?.createdAt ?? createdAt}
          updatedAt={props?.updatedAt ?? updatedAt}
        />
      </TestProvider>
    );
  };

  it('renders created date', () => {
    renderComponent();

    expect(screen.getByText('2 days ago')).toBeInTheDocument();
    expect(formatRelativeDate).toHaveBeenCalledWith(createdAt);
  });

  it('shows modified date when updated date is different', () => {
    vi.mocked(datesAreDifferent).mockReturnValue(true);
    renderComponent();

    expect(screen.getByText('edited 3 hours ago')).toBeInTheDocument();
    expect(datesAreDifferent).toHaveBeenCalledWith(createdAt, updatedAt);
  });

  it('hides modified date when dates are not meaningfully different', () => {
    vi.mocked(datesAreDifferent).mockReturnValue(false);
    renderComponent();

    expect(screen.queryByText(/edited/i)).not.toBeInTheDocument();
  });

  it('uses full date formatting for tooltip labels', () => {
    renderComponent();

    expect(formatFullDate).toHaveBeenCalledWith(createdAt);
    expect(formatFullDate).toHaveBeenCalledWith(updatedAt);
  });
});
