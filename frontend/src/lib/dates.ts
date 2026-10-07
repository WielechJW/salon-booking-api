import { TZDate, tzOffset } from '@date-fns/tz'
import { format } from 'date-fns'
import { pl } from 'date-fns/locale'

export const money = (value: number) =>
  new Intl.NumberFormat('pl-PL', {
    style: 'currency',
    currency: 'PLN',
    maximumFractionDigits: 2,
  }).format(value)
export const dayInSalon = (timezone: string, value = new Date()) =>
  format(new TZDate(value, timezone), 'yyyy-MM-dd')
export const timeLabel = (value: string, timezone: string) =>
  format(new TZDate(value, timezone), 'HH:mm')
export const dateTimeLabel = (value: string, timezone: string) =>
  format(new TZDate(value, timezone), 'd MMM yyyy, HH:mm', { locale: pl })
export const dayLabel = (value: string) =>
  format(new Date(`${value}T12:00:00`), 'EEEE, d MMMM', { locale: pl })

// datetime-local carries a wall-clock value, not the browser's timezone.
// Reject skipped and repeated times rather than silently choosing a DST offset.
export function localDateTimeToUtc(value: string, timezone: string) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value))
    throw new Error('Podaj poprawną datę i godzinę.')
  const [year, month, day, hour, minute] = value.split(/[-T:]/).map(Number)
  const nominal = Date.UTC(year, month - 1, day, hour, minute)
  const offsets = new Set(
    [-2, 0, 2].map((days) => tzOffset(timezone, new Date(nominal + days * 86_400_000))),
  )
  const candidates = [...offsets]
    .map((offset) => new Date(nominal - offset * 60_000))
    .filter((candidate) => format(new TZDate(candidate, timezone), "yyyy-MM-dd'T'HH:mm") === value)
  if (candidates.length === 0)
    throw new Error('Ta godzina nie istnieje w strefie salonu, np. z powodu zmiany czasu.')
  if (candidates.length > 1)
    throw new Error('Ta godzina występuje dwukrotnie przy zmianie czasu. Wybierz inną godzinę.')
  return candidates[0].toISOString()
}

export const weekdays = [
  'Poniedziałek',
  'Wtorek',
  'Środa',
  'Czwartek',
  'Piątek',
  'Sobota',
  'Niedziela',
]
export const statusLabels = {
  pending: 'Oczekująca',
  confirmed: 'Potwierdzona',
  completed: 'Zakończona',
  cancelled: 'Anulowana',
} as const
