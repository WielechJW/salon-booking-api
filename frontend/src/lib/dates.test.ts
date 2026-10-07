import { describe, expect, it } from 'vitest'
import { dayInSalon, localDateTimeToUtc, timeLabel } from './dates'

describe('salon timezone', () => {
  it('shows the salon day even when UTC is still on the previous day', () => {
    expect(dayInSalon('Europe/Warsaw', new Date('2026-10-06T23:30:00Z'))).toBe('2026-10-07')
    expect(timeLabel('2026-10-06T23:30:00Z', 'Europe/Warsaw')).toBe('01:30')
  })
  it('converts working time using the seasonal offset', () => {
    expect(localDateTimeToUtc('2026-07-07T09:00', 'Europe/Warsaw')).toBe('2026-07-07T07:00:00.000Z')
    expect(localDateTimeToUtc('2026-12-07T09:00', 'Europe/Warsaw')).toBe('2026-12-07T08:00:00.000Z')
  })
  it('rejects a skipped hour at the spring DST transition', () => {
    expect(() => localDateTimeToUtc('2026-03-29T02:30', 'Europe/Warsaw')).toThrow('nie istnieje')
  })
  it('rejects an ambiguous hour at the autumn DST transition', () => {
    expect(() => localDateTimeToUtc('2026-10-25T02:30', 'Europe/Warsaw')).toThrow('dwukrotnie')
  })
})
