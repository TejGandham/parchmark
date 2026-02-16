import { describe, it, expect, vi, afterEach } from 'vitest';
import { formatCompactTime } from '../../utils/compactTime';

describe('formatCompactTime', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  function setNow(iso: string) {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(iso));
  }

  it('returns "now" for dates less than 1 minute ago', () => {
    setNow('2026-02-16T12:00:30Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('now');
  });

  it('returns minutes for < 60 min', () => {
    setNow('2026-02-16T12:05:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('5m');
  });

  it('returns hours for < 24 hours', () => {
    setNow('2026-02-16T14:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('2h');
  });

  it('returns days for < 7 days', () => {
    setNow('2026-02-18T12:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('2d');
  });

  it('returns weeks for < 4 weeks', () => {
    setNow('2026-03-02T12:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('2w');
  });

  it('returns short date for >= 4 weeks', () => {
    setNow('2026-04-01T12:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('Feb 16');
  });

  it('returns "now" for future dates', () => {
    setNow('2026-02-16T12:00:00Z');
    expect(formatCompactTime('2026-02-16T13:00:00Z')).toBe('now');
  });

  it('handles 59 minutes correctly', () => {
    setNow('2026-02-16T12:59:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('59m');
  });

  it('handles exactly 1 hour', () => {
    setNow('2026-02-16T13:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('1h');
  });

  it('handles exactly 1 day', () => {
    setNow('2026-02-17T12:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('1d');
  });

  it('handles exactly 1 week', () => {
    setNow('2026-02-23T12:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('1w');
  });

  it('handles 3 weeks', () => {
    setNow('2026-03-09T12:00:00Z');
    expect(formatCompactTime('2026-02-16T12:00:00Z')).toBe('3w');
  });
});
