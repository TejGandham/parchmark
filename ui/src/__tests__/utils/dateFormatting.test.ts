import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  datesAreDifferent,
  formatFullDate,
  formatRelativeDate,
  formatShortDate,
} from '../../utils/dateFormatting';

describe('dateFormatting utilities', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-07T12:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('formatRelativeDate', () => {
    it('returns "just now" for dates less than 60 seconds ago', () => {
      expect(formatRelativeDate('2026-02-07T11:59:30.000Z')).toBe('just now');
    });

    it('returns relative minutes for dates less than 1 hour ago', () => {
      expect(formatRelativeDate('2026-02-07T11:57:00.000Z')).toBe(
        '3 minutes ago'
      );
    });

    it('returns relative hours for dates less than 1 day ago', () => {
      expect(formatRelativeDate('2026-02-07T10:00:00.000Z')).toBe(
        '2 hours ago'
      );
    });

    it('returns relative days for dates less than 1 week ago', () => {
      expect(formatRelativeDate('2026-02-05T12:00:00.000Z')).toBe('2 days ago');
    });

    it('returns short date for dates older than 1 week', () => {
      expect(formatRelativeDate('2025-12-20T12:00:00.000Z')).toBe(
        'Dec 20, 2025'
      );
    });
  });

  describe('formatShortDate', () => {
    it('returns "Mon D" for dates in the same year', () => {
      expect(formatShortDate('2026-01-05T12:00:00.000Z')).toBe('Jan 5');
    });

    it('returns "Mon D, YYYY" for dates in a different year', () => {
      expect(formatShortDate('2025-12-31T12:00:00.000Z')).toBe('Dec 31, 2025');
    });
  });

  describe('formatFullDate', () => {
    it('returns full formatted date string', () => {
      const iso = '2025-03-02T16:45:00.000Z';
      const expected = new Date(iso).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });

      expect(formatFullDate(iso)).toBe(expected);
    });
  });

  describe('datesAreDifferent', () => {
    it('returns true when timestamps are more than 60 seconds apart', () => {
      expect(
        datesAreDifferent(
          '2026-02-07T12:00:00.000Z',
          '2026-02-07T11:58:59.000Z'
        )
      ).toBe(true);
    });

    it('returns false when timestamps are exactly 60 seconds apart', () => {
      expect(
        datesAreDifferent(
          '2026-02-07T12:00:00.000Z',
          '2026-02-07T11:59:00.000Z'
        )
      ).toBe(false);
    });

    it('returns false when timestamps are less than 60 seconds apart', () => {
      expect(
        datesAreDifferent(
          '2026-02-07T12:00:00.000Z',
          '2026-02-07T11:59:45.000Z'
        )
      ).toBe(false);
    });
  });
});
